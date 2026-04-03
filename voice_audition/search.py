"""
Two-stage voice search across the catalog.

Stage 1: Hard filter (provider, gender, language, latency, cost) → narrows to candidates
Stage 2: Claude reads candidates and picks the best matches (semantic matching via the LLM)

The skill calls stage 1 to get a filtered list, then puts those into its context
for Claude to reason over. No embeddings, no vector DB needed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATALOG_DIR = Path(__file__).parent.parent / "catalog"


def load_catalog() -> list[dict]:
    """Load all voice catalog files into a single list."""
    voices = []
    for f in sorted(CATALOG_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            if isinstance(data, list):
                voices.extend(data)
        except (json.JSONDecodeError, OSError):
            continue
    return voices


def filter_voices(
    voices: list[dict] | None = None,
    provider: str | None = None,
    gender: str | None = None,
    language: str | None = None,
    latency_tier: str | None = None,
    max_cost_per_min: float | None = None,
    accent: str | None = None,
    age: str | None = None,
    use_case: str | None = None,
    has_traits: bool = False,
) -> list[dict]:
    """
    Stage 1: Hard filter. Returns voices matching all specified criteria.
    Pass None for any filter to skip it.
    """
    if voices is None:
        voices = load_catalog()

    results = voices

    if provider:
        provider_lower = provider.lower()
        results = [v for v in results if v["provider"] == provider_lower]

    if gender:
        gender_lower = gender.lower()
        results = [v for v in results if v["gender"] == gender_lower or v["gender"] == "unknown"]

    if language:
        lang_lower = language.lower()[:2]
        results = [v for v in results if lang_lower in v.get("languages", []) or v.get("language", "") == lang_lower]

    if latency_tier:
        tier_lower = latency_tier.lower()
        # "fastest" matches only fastest; "fast" matches fastest and fast; "standard" matches all
        tier_order = {"fastest": ["fastest"], "fast": ["fastest", "fast"], "standard": ["fastest", "fast", "standard"]}
        allowed = tier_order.get(tier_lower, ["fastest", "fast", "standard"])
        results = [v for v in results if v.get("latency_tier", "standard") in allowed]

    if max_cost_per_min is not None:
        results = [v for v in results if (v.get("cost_per_min_usd") or 0) <= max_cost_per_min]

    if accent:
        accent_lower = accent.lower()
        results = [v for v in results if v.get("accent", "unknown") == accent_lower or v.get("accent") == "unknown"]

    if age:
        age_lower = age.lower()
        results = [v for v in results if v.get("age", "unknown") == age_lower or v.get("age") == "unknown"]

    if use_case:
        use_case_lower = use_case.lower()
        results = [v for v in results if use_case_lower in v.get("use_cases", [])]

    if has_traits:
        results = [v for v in results if v.get("traits", {}).get("warmth") is not None]

    return results


def format_for_context(voices: list[dict], max_voices: int = 50) -> str:
    """
    Format filtered voices as a compact text block that fits in Claude's context.
    This is what the skill feeds to Claude for Stage 2 (semantic matching).
    """
    if len(voices) > max_voices:
        # Prefer voices with traits data, then by provider diversity
        with_traits = [v for v in voices if v.get("traits", {}).get("warmth") is not None]
        without_traits = [v for v in voices if v.get("traits", {}).get("warmth") is None]
        voices = with_traits[:max_voices] if len(with_traits) >= max_voices else with_traits + without_traits[:max_voices - len(with_traits)]

    lines = [f"FILTERED VOICES ({len(voices)} candidates):\n"]
    for v in voices:
        traits = v.get("traits", {})
        trait_str = ""
        if traits.get("warmth") is not None:
            trait_str = f" | W:{traits['warmth']} E:{traits['energy']} C:{traits['clarity']} A:{traits['authority']} F:{traits['friendliness']}"

        tags_str = ", ".join(v.get("tags", [])[:5]) if v.get("tags") else ""
        use_str = ", ".join(v.get("use_cases", [])[:3]) if v.get("use_cases") else ""
        personality_str = ", ".join(v.get("personality", [])[:3]) if v.get("personality") else ""

        preview = f" | Preview: {v['preview_url']}" if v.get("preview_url") else ""
        cost = f"${v['cost_per_min_usd']:.3f}/min" if v.get("cost_per_min_usd") else "?"

        lines.append(
            f"- **{v['name']}** ({v['provider']}) | {v['gender']}, {v['age']}, {v['accent']}"
            f" | {v['latency_tier']} latency | {cost}"
            f"{trait_str}"
            f"\n  ID: {v['provider_voice_id']}"
            f"\n  {v.get('description', '')}"
            f"{f' | Uses: {use_str}' if use_str else ''}"
            f"{f' | Personality: {personality_str}' if personality_str else ''}"
            f"{f' | Tags: {tags_str}' if tags_str else ''}"
            f"{preview}"
            f"\n  Pipecat: {v.get('pipecat_class', 'N/A')}"
        )

    return "\n".join(lines)


def catalog_summary() -> dict:
    """Return a summary of the catalog for quick overview."""
    voices = load_catalog()
    by_provider = {}
    for v in voices:
        p = v["provider"]
        if p not in by_provider:
            by_provider[p] = 0
        by_provider[p] += 1

    return {
        "total_voices": len(voices),
        "by_provider": by_provider,
        "providers": list(by_provider.keys()),
    }
