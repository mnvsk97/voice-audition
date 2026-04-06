import json

from audition import CATALOG_DIR


def load_all_voices() -> list[dict]:
    voices = []
    if not CATALOG_DIR.exists():
        return voices
    for f in sorted(CATALOG_DIR.glob("*.json")):
        if f.name in ("providers.json", "hosting.json"):
            continue
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, list):
            voices.extend(data)
    return voices


def filter_voices(
    voices: list[dict], *,
    provider: str | None = None, gender: str | None = None,
    language: str | None = None, accent: str | None = None,
    age_group: str | None = None, use_case: str | None = None,
    style_tag: str | None = None, has_preview: bool | None = None,
) -> list[dict]:
    filtered = []
    for v in voices:
        if provider and v.get("provider") != provider:
            continue
        if gender and v.get("gender") != gender and v.get("gender") != "unknown":
            continue
        if language:
            if language != v.get("language", "") and language not in v.get("additional_languages", []):
                continue
        if accent and v.get("accent") and accent.lower() != v.get("accent", "").lower():
            continue
        if age_group and v.get("age_group") != age_group and v.get("age_group") != "unknown":
            continue
        if use_case and use_case not in v.get("use_cases", []):
            continue
        if style_tag and style_tag not in v.get("style_tags", []):
            continue
        if has_preview is True and not v.get("preview_url"):
            continue
        filtered.append(v)
    return filtered


def show_stats():
    voices = load_all_voices()
    total = len(voices)
    enriched = sum(1 for v in voices if _is_enriched(v))

    by_provider: dict[str, int] = {}
    by_gender: dict[str, int] = {}
    for v in voices:
        by_provider[v.get("provider", "unknown")] = by_provider.get(v.get("provider", "unknown"), 0) + 1
        g = v.get("gender", "unknown") or "unknown"
        by_gender[g] = by_gender.get(g, 0) + 1

    print(f"Voice Catalog: {total} voices ({enriched} enriched, {total - enriched} unenriched)")
    print("\n  By provider:")
    for p in sorted(by_provider, key=lambda k: -by_provider[k]):
        print(f"    {p}: {by_provider[p]}")
    print("\n  By gender:")
    for g in sorted(by_gender, key=lambda k: -by_gender[k]):
        print(f"    {g}: {by_gender[g]}")


def _is_enriched(v: dict) -> bool:
    desc = v.get("description") or ""
    if len(desc) < 20:
        return False
    if v.get("gender") == "unknown" and v.get("metadata_source") in ("provider_api", None):
        return False
    return True
