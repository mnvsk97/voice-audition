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

CATALOG_DIR = Path(__file__).resolve().parent.parent.parent / "catalog"
PROVIDERS_FILE = CATALOG_DIR / "providers.json"


def load_all_voices() -> list[dict]:
    """Load all voices from all provider catalog files."""
    voices = []
    if not CATALOG_DIR.exists():
        return voices

    for f in sorted(CATALOG_DIR.glob("*.json")):
        if f.name in ("providers.json", "schema.json"):
            continue
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, list):
            voices.extend(data)

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
        if provider and v.get("provider") != provider:
            continue

        if gender and v.get("gender") != gender and v.get("gender") != "unknown":
            continue

        if language:
            v_lang = v.get("language", "")
            v_additional = v.get("additional_languages", [])
            if language != v_lang and language not in v_additional:
                continue

        if accent and v.get("accent") and accent.lower() != v.get("accent", "").lower():
            continue

        if age_group and v.get("age_group") != age_group and v.get("age_group") != "unknown":
            continue

        if max_cost_tier:
            p = providers_data.get(v.get("provider"), {})
            v_cost = p.get("pricing", {}).get("cost_tier", "medium")
            if cost_order.get(v_cost, 1) > cost_order.get(max_cost_tier, 2):
                continue

        if max_latency_tier:
            p = providers_data.get(v.get("provider"), {})
            v_latency = p.get("technical", {}).get("latency_tier", "fast")
            if latency_order.get(v_latency, 1) > latency_order.get(max_latency_tier, 2):
                continue

        if use_case and use_case not in v.get("use_cases", []):
            continue

        if style_tag and style_tag not in v.get("style_tags", []):
            continue

        if has_preview is True and not v.get("preview_url"):
            continue

        filtered.append(v)

    return filtered


def prepare_for_context(voices: list[dict], max_voices: int = 200) -> str:
    """Format filtered voices as a compact text block for Claude's context.

    Strips provider_metadata and other bulky fields to keep it tight.
    Sorts by popularity (if available) so best-known voices come first.
    """
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


def show_stats():
    """Print catalog statistics."""
    voices = load_all_voices()
    total = len(voices)

    def _is_enriched(v):
        desc = v.get("description") or ""
        if len(desc) < 20:
            return False
        if v.get("gender") == "unknown" and v.get("metadata_source") in ("provider_api", None):
            return False
        return True

    enriched = [v for v in voices if _is_enriched(v)]
    n_enriched = len(enriched)
    n_unenriched = total - n_enriched

    pct_enriched = (n_enriched / total * 100) if total else 0
    pct_unenriched = (n_unenriched / total * 100) if total else 0

    # By provider
    by_provider: dict[str, int] = {}
    for v in voices:
        p = v.get("provider", "unknown")
        by_provider[p] = by_provider.get(p, 0) + 1

    # By gender
    by_gender: dict[str, int] = {}
    for v in voices:
        g = v.get("gender", "unknown") or "unknown"
        by_gender[g] = by_gender.get(g, 0) + 1

    print("Voice Catalog Stats")
    print(f"  Total voices:  {total}")
    print(f"  Enriched:      {n_enriched} ({pct_enriched:.1f}%)")
    print(f"  Unenriched:    {n_unenriched} ({pct_unenriched:.1f}%)")
    print()
    print("  By provider:")
    for p in sorted(by_provider, key=lambda k: -by_provider[k]):
        print(f"    {p}:  {by_provider[p]}")
    print()
    print("  By gender:")
    for g in sorted(by_gender, key=lambda k: -by_gender[k]):
        print(f"    {g}:  {by_gender[g]}")


def run_search(query: str):
    """Simple keyword search across name, description, and tags. Prints results."""
    voices = load_all_voices()
    query_lower = query.lower()
    terms = query_lower.split()

    matches = []
    for v in voices:
        searchable = " ".join([
            v.get("name", ""),
            v.get("description", "") or "",
            " ".join(v.get("style_tags", [])),
            " ".join(v.get("personality_tags", [])),
            " ".join(v.get("use_cases", [])),
            v.get("gender", ""),
            v.get("accent", "") or "",
            v.get("provider", ""),
        ]).lower()

        if all(t in searchable for t in terms):
            matches.append(v)

    if not matches:
        print(f"No voices found for '{query}'")
        return

    print(f"Found {len(matches)} voice(s) for '{query}':\n")
    for v in matches[:30]:
        desc = v.get("description", "") or ""
        if len(desc) > 80:
            desc = desc[:77] + "..."
        tags = v.get("style_tags", [])
        tag_str = f"  tags: {', '.join(tags[:4])}" if tags else ""
        print(f"  {v['name']} ({v['provider']}) [{v.get('gender','?')}] {desc}{tag_str}")

    if len(matches) > 30:
        print(f"\n  ... and {len(matches) - 30} more")


if __name__ == "__main__":
    show_stats()
