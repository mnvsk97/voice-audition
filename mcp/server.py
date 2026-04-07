from __future__ import annotations

from fastmcp import FastMCP

from audition.costs import calculate_voice_costs as _calculate_voice_costs
from audition.db import get_acoustic_features, get_embedding, get_voice as _get_voice
from audition.index import search_voices as _search_voices
from audition.search import filter_voices as _filter_voices, load_all_voices

mcp = FastMCP("VoiceAudition")


def _simplify(v: dict, **extra) -> dict:
    out = {
        k: v.get(k)
        for k in ("id", "name", "provider", "gender", "description", "effective_cost_per_min_usd", "effective_latency_tier")
    }
    out.update(extra)
    return out


@mcp.tool
def search_voices(query: str, top_k: int = 5, gender: str | None = None,
                  provider: str | None = None, min_f0_hz: float | None = None,
                  max_f0_hz: float | None = None) -> list[dict]:
    """Search voices using natural language. Examples: "warm female for healthcare", "deep male British"."""
    filters = {}
    if gender:
        filters["gender"] = gender
    if provider:
        filters["provider"] = provider
    results = _search_voices(query, top_k=top_k, filters=filters)["results"]
    voice_map = {voice["id"]: voice for voice in load_all_voices()}
    simplified = []
    for result in results:
        voice = voice_map.get(result.get("id")) if result.get("metadata") else result
        if voice:
            simplified.append(_simplify(voice, score=result.get("score")))

    if min_f0_hz is None and max_f0_hz is None:
        return simplified

    filtered = []
    for voice in simplified:
        features = get_acoustic_features(voice["id"])
        f0 = None if not features else features.get("f0_mean_hz")
        if f0 is None:
            continue
        if min_f0_hz is not None and f0 < min_f0_hz:
            continue
        if max_f0_hz is not None and f0 > max_f0_hz:
            continue
        filtered.append({**voice, "f0_mean_hz": f0})
    return filtered


@mcp.tool
def get_voice(voice_id: str) -> dict | None:
    """Get full details for a voice by ID (e.g. 'openai:shimmer', 'rime:mist:bayou')."""
    voice = _get_voice(voice_id)
    if voice:
        return {k: val for k, val in voice.items() if k != "provider_metadata"}
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
    acoustic = 0
    clap = 0
    for v in voices:
        by_provider[v.get("provider", "?")] = by_provider.get(v.get("provider", "?"), 0) + 1
        g = v.get("gender", "unknown") or "unknown"
        by_gender[g] = by_gender.get(g, 0) + 1
        desc = v.get("description") or ""
        if len(desc) >= 20 and not (v.get("gender") == "unknown" and v.get("metadata_source") in ("provider_api", None)):
            enriched += 1
        if get_acoustic_features(v["id"]):
            acoustic += 1
        if get_embedding(v["id"]) is not None:
            clap += 1
    return {
        "total": len(voices),
        "enriched": enriched,
        "acoustic": acoustic,
        "embedded": clap,
        "by_provider": by_provider,
        "by_gender": by_gender,
    }


@mcp.tool
def calculate_voice_costs(minutes_per_month: int) -> dict:
    """Compare API vs self-hosted costs at a given monthly volume."""
    return _calculate_voice_costs(minutes_per_month)


@mcp.tool
def analyze_voices(brief: str, num_candidates: int = 8, gender: str | None = None,
                   provider: str | None = None) -> dict:
    """Analyze top voice options without generating audio."""
    from audition.analyze import analyze_brief

    filters = {}
    if gender:
        filters["gender"] = gender
    if provider:
        filters["provider"] = provider
    return analyze_brief(brief, num_candidates=num_candidates, filters=filters)


@mcp.tool
def find_similar_voices(voice_id: str, top_k: int = 5) -> list[dict]:
    """Find acoustically similar voices using stored embeddings."""
    from audition.index import search_similar_voices

    return [_simplify(v, score=v.get("score")) for v in search_similar_voices(voice_id, top_k=top_k)]


@mcp.tool
def get_acoustic_profile(voice_id: str) -> dict | None:
    """Get the measured acoustic profile for a voice."""
    from audition.index import acoustic_profile_summary

    return acoustic_profile_summary(voice_id)


@mcp.tool
def run_voice_audition(brief: str, num_candidates: int = 8, gender: str | None = None,
                       provider: str | None = None, mode: str = "ai") -> dict:
    """Run a voice audition. Returns candidates ranked by fit for the use case."""
    from audition.audition import run_audition
    return run_audition(brief, num_candidates=num_candidates, gender=gender, provider=provider, mode=mode)


def run_mcp():
    mcp.run()
