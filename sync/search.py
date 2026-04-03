"""
Voice catalog search module.

Two-stage search:
1. Hard filter: provider, gender, language, latency_tier, cost_tier, age_group, accent
2. Semantic match: Claude reads filtered candidates + user requirements, picks best 3-4

This module handles stage 1. Stage 2 happens in the skill (Claude does the matching).
The output of stage 1 is a subset of the catalog that fits in Claude's context window.
"""

import json
from pathlib import Path

CATALOG_DIR = Path(__file__).parent.parent / "catalog" / "voices"
PROVIDERS_FILE = Path(__file__).parent.parent / "catalog" / "providers.json"


def load_all_voices() -> list[dict]:
    """Load all voices from all provider catalog files."""
    voices = []
    if not CATALOG_DIR.exists():
        return voices

    for f in sorted(CATALOG_DIR.glob("*.json")):
        data = json.loads(f.read_text())
        voices.extend(data.get("voices", []))

    return voices


def load_providers() -> dict:
    """Load provider profiles."""
    if not PROVIDERS_FILE.exists():
        return {}
    data = json.loads(PROVIDERS_FILE.read_text())
    return data.get("providers", {})


def filter_voices(
    voices: list[dict],
    *,
    provider: str | None = None,
    gender: str | None = None,
    language: str | None = None,
    accent: str | None = None,
    age_group: str | None = None,
    max_cost_tier: str | None = None,
    max_latency_tier: str | None = None,
    use_case: str | None = None,
    style_tag: str | None = None,
    has_preview: bool | None = None,
) -> list[dict]:
    """Stage 1: Hard filter voices by constraints.

    Returns a subset that matches ALL specified criteria.
    Unspecified criteria are ignored (pass-through).
    """
    providers_data = load_providers()

    cost_order = {"low": 0, "medium": 1, "high": 2}
    latency_order = {"fastest": 0, "fast": 1, "standard": 2}

    filtered = []

    for v in voices:
        # Provider filter
        if provider and v.get("provider") != provider:
            continue

        # Gender filter
        if gender and v.get("gender") != gender and v.get("gender") != "unknown":
            continue

        # Language filter
        if language:
            v_lang = v.get("language", "")
            v_additional = v.get("additional_languages", [])
            if language != v_lang and language not in v_additional:
                continue

        # Accent filter
        if accent and v.get("accent") and accent.lower() != v.get("accent", "").lower():
            continue

        # Age group filter
        if age_group and v.get("age_group") != age_group and v.get("age_group") != "unknown":
            continue

        # Cost tier filter (from provider profile)
        if max_cost_tier:
            p = providers_data.get(v.get("provider"), {})
            v_cost = p.get("pricing", {}).get("cost_tier", "medium")
            if cost_order.get(v_cost, 1) > cost_order.get(max_cost_tier, 2):
                continue

        # Latency tier filter (from provider profile)
        if max_latency_tier:
            p = providers_data.get(v.get("provider"), {})
            v_latency = p.get("technical", {}).get("latency_tier", "fast")
            if latency_order.get(v_latency, 1) > latency_order.get(max_latency_tier, 2):
                continue

        # Use case filter
        if use_case and use_case not in v.get("use_cases", []):
            continue

        # Style tag filter
        if style_tag and style_tag not in v.get("style_tags", []):
            continue

        # Preview availability filter
        if has_preview is True and not v.get("preview_url"):
            continue

        filtered.append(v)

    return filtered


def prepare_for_context(voices: list[dict], max_voices: int = 200) -> str:
    """Format filtered voices as a compact text block for Claude's context.

    Strips provider_metadata and other bulky fields to keep it tight.
    Sorts by popularity (if available) so best-known voices come first.
    """
    # Sort: voices with popularity scores first (descending), then alphabetical
    def sort_key(v):
        pop = v.get("popularity_score") or 0
        return (-pop, v.get("name", ""))

    sorted_voices = sorted(voices, key=sort_key)[:max_voices]

    lines = []
    for v in sorted_voices:
        traits = v.get("traits", {})
        trait_str = ""
        if any(traits.get(k) is not None for k in ["warmth", "energy", "clarity", "authority", "friendliness"]):
            parts = []
            for k in ["warmth", "energy", "clarity", "authority", "friendliness"]:
                val = traits.get(k)
                if val is not None:
                    parts.append(f"{k}={val}")
            trait_str = f" | Traits: {', '.join(parts)}"

        tags = v.get("style_tags", []) + v.get("personality_tags", [])
        tag_str = f" | Tags: {', '.join(tags[:6])}" if tags else ""

        use_str = f" | For: {', '.join(v.get('use_cases', [])[:4])}" if v.get("use_cases") else ""

        preview = f" | Preview: {v['preview_url']}" if v.get("preview_url") else ""

        desc = v.get("description", "") or ""
        if len(desc) > 120:
            desc = desc[:117] + "..."

        lines.append(
            f"- **{v['name']}** ({v['provider']}) [{v.get('gender','?')}, {v.get('age_group','?')}, {v.get('accent','?')}] "
            f"ID: `{v['provider_voice_id']}`{trait_str}{tag_str}{use_str}{preview}"
            f"\n  {desc}" if desc else ""
        )

    return f"## {len(sorted_voices)} voices (filtered from {len(voices)} total)\n\n" + "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    voices = load_all_voices()
    print(f"Total voices loaded: {len(voices)}")

    # Test filter
    female_healthcare = filter_voices(voices, gender="female", use_case="healthcare")
    print(f"Female + healthcare: {len(female_healthcare)}")

    fastest = filter_voices(voices, max_latency_tier="fastest")
    print(f"Fastest latency: {len(fastest)}")

    cheap = filter_voices(voices, max_cost_tier="low")
    print(f"Low cost: {len(cheap)}")
