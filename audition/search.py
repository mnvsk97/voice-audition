from audition.db import get_acoustic_features, get_embedding, load_voices


def load_all_voices() -> list[dict]:
    return load_voices()


def filter_voices(
    voices: list[dict], *,
    provider: str | None = None, gender: str | None = None,
    language: str | None = None, accent: str | None = None,
    age_group: str | None = None, use_case: str | None = None,
    style_tag: str | None = None, has_preview: bool | None = None,
) -> list[dict]:
    filtered = []
    for voice in voices:
        if provider and voice.get("provider") != provider:
            continue
        if gender and voice.get("gender") != gender and voice.get("gender") != "unknown":
            continue
        if language:
            if language != voice.get("language", "") and language not in voice.get("additional_languages", []):
                continue
        if accent and voice.get("accent") and accent.lower() != voice.get("accent", "").lower():
            continue
        if age_group and voice.get("age_group") != age_group and voice.get("age_group") != "unknown":
            continue
        if use_case and use_case not in voice.get("use_cases", []):
            continue
        if style_tag and style_tag not in voice.get("style_tags", []):
            continue
        if has_preview is True and not voice.get("preview_url"):
            continue
        filtered.append(voice)
    return filtered


def keyword_search(query: str, top_k: int = 5, voices: list[dict] | None = None,
                   filters: dict | None = None) -> list[dict]:
    pool = voices if voices is not None else load_all_voices()
    if filters:
        pool = filter_voices(pool, **filters)
    terms = [term for term in query.lower().split() if term]
    if not terms:
        return []
    scored = []
    for voice in pool:
        searchable = " ".join([
            voice.get("name", ""),
            voice.get("description") or "",
            " ".join(voice.get("use_cases", [])),
            voice.get("gender", "") or "",
            voice.get("accent", "") or "",
            " ".join(voice.get("style_tags", [])),
            " ".join(voice.get("personality_tags", [])),
        ]).lower()
        hits = sum(1 for term in terms if term in searchable)
        if hits:
            scored.append((hits / len(terms), voice))
    scored.sort(key=lambda item: (-item[0], item[1].get("name", "")))
    return [{**voice, "score": round(score, 2)} for score, voice in scored[:top_k]]


def show_stats():
    voices = load_all_voices()
    total = len(voices)
    enriched = sum(1 for voice in voices if _is_enriched(voice))
    acoustic = sum(1 for voice in voices if get_acoustic_features(voice["id"]))
    clap = sum(1 for voice in voices if get_embedding(voice["id"]) is not None)

    by_provider: dict[str, int] = {}
    by_gender: dict[str, int] = {}
    for voice in voices:
        by_provider[voice.get("provider", "unknown")] = by_provider.get(voice.get("provider", "unknown"), 0) + 1
        gender = voice.get("gender", "unknown") or "unknown"
        by_gender[gender] = by_gender.get(gender, 0) + 1

    print(
        f"Voice Catalog: {total} voices "
        f"({enriched} enriched, {acoustic} acoustic, {clap} embedded, {total - enriched} unenriched)"
    )
    print("\n  By provider:")
    for provider in sorted(by_provider, key=lambda key: -by_provider[key]):
        print(f"    {provider}: {by_provider[provider]}")
    print("\n  By gender:")
    for gender in sorted(by_gender, key=lambda key: -by_gender[key]):
        print(f"    {gender}: {by_gender[gender]}")


def _is_enriched(voice: dict) -> bool:
    description = voice.get("description") or ""
    if len(description) < 20:
        return False
    if voice.get("gender") == "unknown" and voice.get("metadata_source") in ("provider_api", None):
        return False
    return True
