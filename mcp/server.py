from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from audition.search import filter_voices as _filter_voices, load_all_voices

mcp = FastMCP("VoiceAudition")


def _simplify(v: dict, **extra) -> dict:
    out = {k: v.get(k) for k in ("id", "name", "provider", "gender", "description")}
    out.update(extra)
    return out


@mcp.tool
def search_voices(query: str, top_k: int = 5, gender: str | None = None,
                  provider: str | None = None) -> list[dict]:
    """Search voices using natural language. Examples: "warm female for healthcare", "deep male British"."""
    filters = {}
    if gender:
        filters["gender"] = gender
    if provider:
        filters["provider"] = provider
    try:
        from audition.index import semantic_search
        results = asyncio.run(semantic_search(query, top_k=top_k, filters=filters))
        return [_simplify(v, score=v.get("score")) for v in results]
    except Exception:
        pass
    # Fallback: keyword search
    voices = _filter_voices(load_all_voices(), **{k: v for k, v in filters.items()})
    terms = query.lower().split()
    scored = []
    for v in voices:
        searchable = " ".join([v.get("name", ""), v.get("description", "") or "",
                               " ".join(v.get("use_cases", [])), v.get("gender", ""),
                               v.get("accent", "") or ""]).lower()
        hits = sum(1 for t in terms if t in searchable)
        if hits > 0:
            scored.append((hits / len(terms), v))
    scored.sort(key=lambda x: -x[0])
    return [_simplify(v, score=round(s, 2)) for s, v in scored[:top_k]]


@mcp.tool
def get_voice(voice_id: str) -> dict | None:
    """Get full details for a voice by ID (e.g. 'openai:shimmer', 'rime:mist:bayou')."""
    for v in load_all_voices():
        if v.get("id") == voice_id:
            return {k: val for k, val in v.items() if k != "provider_metadata"}
    return None


@mcp.tool
def filter_voices(gender: str | None = None, provider: str | None = None,
                  accent: str | None = None, age_group: str | None = None,
                  use_case: str | None = None) -> list[dict]:
    """Filter voices by structured criteria. Max 50 results."""
    kwargs = {k: v for k, v in dict(gender=gender, provider=provider, accent=accent,
                                     age_group=age_group, use_case=use_case).items() if v}
    matched = _filter_voices(load_all_voices(), **kwargs)
    return [_simplify(v, age_group=v.get("age_group"), accent=v.get("accent")) for v in matched[:50]]


@mcp.tool
def get_catalog_stats() -> dict:
    """Voice catalog statistics."""
    voices = load_all_voices()
    by_provider: dict[str, int] = {}
    by_gender: dict[str, int] = {}
    enriched = 0
    for v in voices:
        by_provider[v.get("provider", "?")] = by_provider.get(v.get("provider", "?"), 0) + 1
        g = v.get("gender", "unknown") or "unknown"
        by_gender[g] = by_gender.get(g, 0) + 1
        desc = v.get("description") or ""
        if len(desc) >= 20 and not (v.get("gender") == "unknown" and v.get("metadata_source") in ("provider_api", None)):
            enriched += 1
    return {"total": len(voices), "enriched": enriched, "by_provider": by_provider, "by_gender": by_gender}


@mcp.tool
def run_voice_audition(brief: str, num_candidates: int = 8, gender: str | None = None,
                       provider: str | None = None) -> dict:
    """Run a voice audition. Returns candidates ranked by fit for the use case."""
    from audition.audition import detect_use_case, get_profile, select_candidates
    use_case = detect_use_case(brief)
    profile = get_profile(use_case)
    filters = {}
    if gender:
        filters["gender"] = gender
    if provider:
        filters["provider"] = provider
    candidates = select_candidates(brief, num=num_candidates, filters=filters)
    return {
        "use_case": use_case,
        "criteria": profile["criteria"],
        "candidates": [{"id": c["id"], "name": c.get("name"), "provider": c.get("provider"),
                        "gender": c.get("gender"), "description": c.get("description"),
                        "search_score": c.get("search_score", 0)} for c in candidates],
    }


def run_mcp():
    mcp.run()
