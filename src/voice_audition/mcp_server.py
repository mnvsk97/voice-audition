"""FastMCP server exposing voice catalog search tools."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from voice_audition.search import (
    filter_voices as _filter_voices,
    load_all_voices,
    load_providers,
)

mcp = FastMCP("VoiceAudition")


def _simplify_voice(v: dict, *, include_score: bool = False, extra_fields: tuple[str, ...] = ()) -> dict:
    """Return a compact representation of a voice dict."""
    out = {
        "id": v.get("id"),
        "name": v.get("name"),
        "provider": v.get("provider"),
        "gender": v.get("gender"),
        "description": v.get("description"),
    }
    for f in extra_fields:
        out[f] = v.get(f)
    if include_score and "score" in v:
        out["score"] = v["score"]
    return out


# ---------------------------------------------------------------------------
# Tool 1: search_voices
# ---------------------------------------------------------------------------

@mcp.tool
def search_voices(
    query: str,
    top_k: int = 5,
    gender: str | None = None,
    provider: str | None = None,
    language: str | None = None,
    max_cost_per_min: float | None = None,
    latency_tier: str | None = None,
) -> list[dict]:
    """Search the voice catalog using natural language. Returns top matching voices with scores.

    Examples:
    - "warm female voice for healthcare"
    - "authoritative male, British accent"
    - "calm soothing voice for meditation app"

    Optional filters narrow results before semantic search.
    """
    filters: dict = {}
    if gender is not None:
        filters["gender"] = gender
    if provider is not None:
        filters["provider"] = provider
    if language is not None:
        filters["language"] = language
    if latency_tier is not None:
        filters["max_latency_tier"] = latency_tier

    # Try semantic search via the index module (may not be installed/built yet).
    try:
        from voice_audition.index import semantic_search  # noqa: F811

        results = asyncio.run(semantic_search(query, top_k=top_k, filters=filters))
        return [_simplify_voice(v, include_score=True) for v in results]
    except (ImportError, ModuleNotFoundError, Exception):
        pass

    # Fallback: keyword search over the catalog.
    voices = load_all_voices()
    if filters:
        voices = _filter_voices(voices, **{k: v for k, v in filters.items()})

    query_lower = query.lower()
    terms = query_lower.split()

    scored: list[tuple[int, dict]] = []
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
        hits = sum(1 for t in terms if t in searchable)
        if hits > 0:
            scored.append((hits, v))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_k]
    results = []
    for hits, v in top:
        d = _simplify_voice(v, include_score=True)
        d["score"] = round(hits / len(terms), 2) if terms else 0.0
        results.append(d)
    return results


# ---------------------------------------------------------------------------
# Tool 2: get_voice
# ---------------------------------------------------------------------------

@mcp.tool
def get_voice(voice_id: str) -> dict | None:
    """Get full details for a voice by ID (e.g. 'openai:shimmer', 'rime:mist:bayou')."""
    voices = load_all_voices()
    for v in voices:
        if v.get("id") == voice_id:
            # Return the full voice dict, stripping bulky provider_metadata.
            out = {k: val for k, val in v.items() if k != "provider_metadata"}
            return out
    return None


# ---------------------------------------------------------------------------
# Tool 3: filter_voices
# ---------------------------------------------------------------------------

@mcp.tool
def filter_voices(
    gender: str | None = None,
    provider: str | None = None,
    language: str | None = None,
    accent: str | None = None,
    age_group: str | None = None,
    use_case: str | None = None,
    max_cost_tier: str | None = None,
    max_latency_tier: str | None = None,
) -> list[dict]:
    """Filter voices by structured criteria. Returns all matching voices (max 50).

    Use this for precise filtering when you know exact constraints.
    For natural language queries, use search_voices instead.
    """
    voices = load_all_voices()
    kwargs: dict = {}
    if gender is not None:
        kwargs["gender"] = gender
    if provider is not None:
        kwargs["provider"] = provider
    if language is not None:
        kwargs["language"] = language
    if accent is not None:
        kwargs["accent"] = accent
    if age_group is not None:
        kwargs["age_group"] = age_group
    if use_case is not None:
        kwargs["use_case"] = use_case
    if max_cost_tier is not None:
        kwargs["max_cost_tier"] = max_cost_tier
    if max_latency_tier is not None:
        kwargs["max_latency_tier"] = max_latency_tier

    matched = _filter_voices(voices, **kwargs)
    extra = ("age_group", "accent")
    return [_simplify_voice(v, extra_fields=extra) for v in matched[:50]]


# ---------------------------------------------------------------------------
# Tool 4: get_providers
# ---------------------------------------------------------------------------

@mcp.tool
def get_providers() -> list[dict]:
    """List all TTS providers with reliability scores, pricing, and capabilities."""
    providers = load_providers()
    result = []
    for name, info in providers.items():
        result.append({
            "name": name,
            "reliability_score": info.get("reliability", {}).get("score"),
            "latency_tier": info.get("technical", {}).get("latency_tier"),
            "cost_tier": info.get("pricing", {}).get("cost_tier"),
            "pipecat_supported": info.get("pipecat", {}).get("supported", False),
        })
    return result


# ---------------------------------------------------------------------------
# Tool 5: get_catalog_stats
# ---------------------------------------------------------------------------

@mcp.tool
def get_catalog_stats() -> dict:
    """Get voice catalog statistics -- total voices, enrichment status, provider breakdown."""
    voices = load_all_voices()
    total = len(voices)

    def _is_enriched(v: dict) -> bool:
        desc = v.get("description") or ""
        if len(desc) < 20:
            return False
        if v.get("gender") == "unknown" and v.get("metadata_source") in ("provider_api", None):
            return False
        return True

    enriched = sum(1 for v in voices if _is_enriched(v))

    by_provider: dict[str, int] = {}
    for v in voices:
        p = v.get("provider", "unknown")
        by_provider[p] = by_provider.get(p, 0) + 1

    by_gender: dict[str, int] = {}
    for v in voices:
        g = v.get("gender", "unknown") or "unknown"
        by_gender[g] = by_gender.get(g, 0) + 1

    return {
        "total": total,
        "enriched": enriched,
        "unenriched": total - enriched,
        "by_provider": by_provider,
        "by_gender": by_gender,
    }


# ---------------------------------------------------------------------------
# Tool 6: run_audition
# ---------------------------------------------------------------------------

@mcp.tool
def run_voice_audition(
    brief: str,
    num_candidates: int = 8,
    gender: str | None = None,
    provider: str | None = None,
) -> dict:
    """Run a full voice audition for a use case. Generates test scripts,
    auditions candidates, scores them, and returns a ranked scorecard.

    Examples:
    - "fertility clinic phone agent for anxious IVF patients"
    - "cold calling agent for real estate leads"
    - "meditation app voice, calm and grounding"
    """
    from voice_audition.audition import detect_use_case, get_profile, select_candidates

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
        "scripts": [s["name"] for s in profile["scripts"]],
        "candidates": [
            {
                "id": c["id"],
                "name": c.get("name"),
                "provider": c.get("provider"),
                "gender": c.get("gender"),
                "description": c.get("description"),
                "search_score": c.get("search_score", 0),
            }
            for c in candidates
        ],
        "note": "Full audition with audio generation + scoring requires provider API keys. "
                "Run 'voice-audition audition' CLI command for the complete pipeline.",
    }


# ---------------------------------------------------------------------------
# Tool 7: calculate_voice_costs
# ---------------------------------------------------------------------------

@mcp.tool
def calculate_voice_costs(minutes_per_month: int) -> dict:
    """Calculate and compare API vs self-hosted TTS costs at a given monthly volume.

    Returns cost breakdown for all providers and self-hosted options with recommendation.
    Example: 100000 minutes/month
    """
    from voice_audition.costs import calculate_costs
    return calculate_costs(minutes_per_month)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def run_mcp():
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run_mcp()
