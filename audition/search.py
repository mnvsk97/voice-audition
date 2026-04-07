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


def is_enriched(voice: dict) -> bool:
    description = voice.get("description") or ""
    if len(description) < 20:
        return False
    if voice.get("gender") == "unknown" and voice.get("metadata_source") in ("provider_api", None):
        return False
    return True


def compute_catalog_stats(voices: list[dict] | None = None) -> dict:
    """Compute catalog statistics. Shared by CLI stats and MCP get_catalog_stats."""
    from audition.db import connect_catalog, init_catalog_db

    if voices is None:
        voices = load_all_voices()

    init_catalog_db()
    from audition.db import get_catalog_db_path
    import sqlite3
    conn = sqlite3.connect(get_catalog_db_path())
    conn.row_factory = sqlite3.Row
    try:
        acoustic_rows = conn.execute(
            "SELECT voice_id, utmos_score FROM voice_acoustic_features"
        ).fetchall()
        embedding_ids = {
            row["voice_id"]
            for row in conn.execute(
                "SELECT DISTINCT voice_id FROM voice_embeddings WHERE embedding_kind='clap'"
            ).fetchall()
        }
    finally:
        conn.close()

    acoustic_map = {row["voice_id"]: row for row in acoustic_rows}

    enriched = 0
    acoustic = len(acoustic_map)
    utmos_scored = sum(1 for row in acoustic_rows if row["utmos_score"] is not None)
    clap = len(embedding_ids)
    by_provider: dict[str, int] = {}
    by_gender: dict[str, int] = {}

    for voice in voices:
        if is_enriched(voice):
            enriched += 1
        p = voice.get("provider", "unknown")
        by_provider[p] = by_provider.get(p, 0) + 1
        g = voice.get("gender", "unknown") or "unknown"
        by_gender[g] = by_gender.get(g, 0) + 1

    return {
        "total": len(voices),
        "enriched": enriched,
        "acoustic": acoustic,
        "utmos_scored": utmos_scored,
        "embedded": clap,
        "by_provider": by_provider,
        "by_gender": by_gender,
    }


def show_stats():
    voices = load_all_voices()
    s = compute_catalog_stats(voices)
    print(
        f"Voice Catalog: {s['total']} voices "
        f"({s['enriched']} enriched, {s['acoustic']} acoustic, {s['utmos_scored']} quality-scored, "
        f"{s['embedded']} embedded, {s['total'] - s['enriched']} unenriched)"
    )
    print("\n  By provider:")
    for provider in sorted(s["by_provider"], key=lambda k: -s["by_provider"][k]):
        print(f"    {provider}: {s['by_provider'][provider]}")
    print("\n  By gender:")
    for gender in sorted(s["by_gender"], key=lambda k: -s["by_gender"][k]):
        print(f"    {gender}: {s['by_gender'][gender]}")
