from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from audition.audition import detect_use_case, get_profile, select_candidates
from audition.db import cache_query_result, create_analysis_run, get_acoustic_features, get_cached_query, make_cache_key


class AnalyzeState(TypedDict):
    brief: str
    num_candidates: int
    filters: dict
    use_case: str
    profile: dict
    candidates: list[dict]
    scored_candidates: list[dict]
    analysis: dict


_CRITERIA_TO_TRAITS = {
    "patient_comfort": ["warmth", "friendliness"],
    "trust": ["authority", "confidence"],
    "empathy": ["warmth", "friendliness"],
    "clarity": ["clarity"],
    "pacing": [],
    "sensitivity": ["warmth"],
    "energy": ["energy"],
    "rapport": ["friendliness", "warmth"],
    "persuasiveness": ["confidence", "authority"],
    "resilience": ["confidence"],
    "likability": ["friendliness", "warmth"],
    "helpfulness": ["friendliness", "clarity"],
    "professionalism": ["authority", "clarity"],
    "resolution_focus": ["confidence", "clarity"],
    "authority": ["authority"],
    "precision": ["clarity"],
    "trustworthiness": ["confidence", "authority"],
    "calm": ["warmth"],
    "compliance_tone": ["authority"],
    "spaciousness": [],
    "grounding": ["warmth"],
    "non_intrusive": ["warmth"],
    "breath_quality": [],
    "presence": ["confidence"],
    "patience": ["warmth"],
    "encouragement": ["friendliness", "warmth"],
    "structure": ["clarity"],
    "fit": ["warmth", "clarity", "confidence"],
}


def _detect_use_case_node(state: AnalyzeState) -> dict:
    use_case = detect_use_case(state["brief"])
    return {"use_case": use_case, "profile": get_profile(use_case)}


def _search_candidates_node(state: AnalyzeState) -> dict:
    candidates = select_candidates(
        state["brief"],
        num=state["num_candidates"],
        filters=state.get("filters") or None,
    )
    return {"candidates": candidates}


_USE_CASE_ACOUSTIC_PROFILES = {
    "healthcare": {"f0_range": (100, 220), "rate_range": (2.5, 4.0), "hnr_min": 15},
    "sales": {"f0_range": (100, 250), "rate_range": (3.5, 5.5), "hnr_min": 12},
    "customer_support": {"f0_range": (100, 240), "rate_range": (3.0, 4.5), "hnr_min": 14},
    "finance": {"f0_range": (80, 200), "rate_range": (2.5, 4.0), "hnr_min": 16},
    "meditation": {"f0_range": (80, 180), "rate_range": (1.5, 3.0), "hnr_min": 18},
    "education": {"f0_range": (100, 240), "rate_range": (2.5, 4.5), "hnr_min": 14},
}


def _range_score(value: float | None, low: float, high: float) -> float:
    """Score 1.0 if in range, degrade linearly outside. Returns 0.5 if value is None."""
    if value is None:
        return 0.5
    if low <= value <= high:
        return 1.0
    span = high - low
    if value < low:
        return max(0.0, 1.0 - (low - value) / (span or 1.0))
    return max(0.0, 1.0 - (value - high) / (span or 1.0))


def _compute_quality_score(candidate: dict, features: dict | None) -> float:
    """Combine UTMOS (voice-level) and provider ELO (model-level) into 0-1 score."""
    utmos = features.get("utmos_score") if features else None
    elo = candidate.get("effective_quality_elo")

    utmos_norm = utmos / 5.0 if utmos is not None else None
    elo_norm = min(1.0, elo / 1200.0) if elo is not None else None

    if utmos_norm is not None and elo_norm is not None:
        return utmos_norm * 0.6 + elo_norm * 0.4
    if utmos_norm is not None:
        return utmos_norm
    if elo_norm is not None:
        return elo_norm
    return 0.5


def _compute_acoustic_fit(features: dict | None, use_case: str) -> float:
    """Check if voice acoustic profile matches use case expectations."""
    profile = _USE_CASE_ACOUSTIC_PROFILES.get(use_case)
    if not profile or not features:
        return 0.5

    scores = []
    f0_low, f0_high = profile["f0_range"]
    scores.append(_range_score(features.get("f0_mean_hz"), f0_low, f0_high))

    rate_low, rate_high = profile["rate_range"]
    scores.append(_range_score(features.get("speech_rate_syl_per_sec"), rate_low, rate_high))

    hnr = features.get("hnr_db")
    if hnr is not None:
        scores.append(min(1.0, hnr / profile["hnr_min"]) if profile["hnr_min"] else 0.5)
    else:
        scores.append(0.5)

    return sum(scores) / len(scores)


def _score_candidate(candidate: dict, profile: dict, use_case: str = "general") -> dict:
    traits = candidate.get("traits") or {}
    criteria = profile.get("criteria", [])
    features = get_acoustic_features(candidate["id"])

    trait_scores = []
    for criterion in criteria:
        mapped = _CRITERIA_TO_TRAITS.get(criterion, [])
        values = [traits.get(name) for name in mapped if traits.get(name) is not None]
        if values:
            trait_scores.append(sum(values) / len(values))

    trait_component = (sum(trait_scores) / len(trait_scores)) if trait_scores else 0.5
    search_component = candidate.get("search_score", 0.0)
    quality_component = _compute_quality_score(candidate, features)
    acoustic_fit_component = _compute_acoustic_fit(features, use_case)
    cost = candidate.get("effective_cost_per_min_usd")
    latency = candidate.get("effective_latency_tier")

    cost_component = 0.5
    if isinstance(cost, (int, float)):
        cost_component = max(0.0, min(1.0, 1.0 - (float(cost) / 0.05)))

    latency_component = {
        "fastest": 1.0,
        "fast": 0.85,
        "normal": 0.65,
        "slow": 0.4,
    }.get((latency or "").lower(), 0.5)

    total = round(
        (search_component * 0.35)
        + (quality_component * 0.25)
        + (trait_component * 0.15)
        + (acoustic_fit_component * 0.10)
        + (cost_component * 0.10)
        + (latency_component * 0.05),
        4,
    )

    rationale = []
    utmos = features.get("utmos_score") if features else None
    if utmos is not None:
        rationale.append(f"MOS={utmos:.2f}")
    elo = candidate.get("effective_quality_elo")
    if elo is not None:
        rationale.append(f"ELO={elo}")
    if candidate.get("effective_cost_per_min_usd") is not None:
        rationale.append(f"cost ${candidate['effective_cost_per_min_usd']:.3f}/min")
    if candidate.get("effective_latency_tier"):
        rationale.append(f"latency {candidate['effective_latency_tier']}")
    if candidate.get("description"):
        rationale.append(candidate["description"])

    return {
        **candidate,
        "analysis_score": total,
        "analysis_notes": "; ".join(rationale),
    }


def _score_candidates_node(state: AnalyzeState) -> dict:
    use_case = state.get("use_case", "general")
    scored = [_score_candidate(c, state["profile"], use_case) for c in state["candidates"]]
    scored.sort(key=lambda item: (-item["analysis_score"], item.get("name", "")))
    return {"scored_candidates": scored}


def _summarize_node(state: AnalyzeState) -> dict:
    scored = state["scored_candidates"]
    if not scored:
        return {"analysis": {"use_case": state["use_case"], "shortlist": [], "message": "No candidates found."}}

    best_overall = scored[0]
    budget_sorted = sorted(scored, key=lambda item: (item.get("effective_cost_per_min_usd") is None, item.get("effective_cost_per_min_usd") or 9999, -item["analysis_score"]))
    best_budget = budget_sorted[0]
    safest = max(scored, key=lambda item: ((item.get("traits") or {}).get("clarity") or 0) + ((item.get("traits") or {}).get("authority") or 0))

    analysis = {
        "use_case": state["use_case"],
        "criteria": state["profile"].get("criteria", []),
        "best_overall": {
            "id": best_overall["id"],
            "name": best_overall.get("name"),
            "provider": best_overall.get("provider"),
            "score": best_overall["analysis_score"],
            "cost_per_min_usd": best_overall.get("effective_cost_per_min_usd"),
            "why": best_overall.get("analysis_notes"),
        },
        "best_budget": {
            "id": best_budget["id"],
            "name": best_budget.get("name"),
            "provider": best_budget.get("provider"),
            "score": best_budget["analysis_score"],
            "cost_per_min_usd": best_budget.get("effective_cost_per_min_usd"),
            "why": best_budget.get("analysis_notes"),
        },
        "safest_option": {
            "id": safest["id"],
            "name": safest.get("name"),
            "provider": safest.get("provider"),
            "score": safest["analysis_score"],
            "cost_per_min_usd": safest.get("effective_cost_per_min_usd"),
            "why": safest.get("analysis_notes"),
        },
        "shortlist": [
            {
                "id": item["id"],
                "name": item.get("name"),
                "provider": item.get("provider"),
                "score": item["analysis_score"],
                "cost_per_min_usd": item.get("effective_cost_per_min_usd"),
                "latency_tier": item.get("effective_latency_tier"),
                "notes": item.get("analysis_notes"),
            }
            for item in scored[: min(5, len(scored))]
        ],
        "next_step": "Use audition --mode ai for automatic ranking or audition --mode human to generate clips for manual review.",
    }
    return {"analysis": analysis}


def build_analysis_graph():
    return (
        StateGraph(AnalyzeState)
        .add_node("detect_use_case", _detect_use_case_node)
        .add_node("search_candidates", _search_candidates_node)
        .add_node("score_candidates", _score_candidates_node)
        .add_node("summarize", _summarize_node)
        .add_edge(START, "detect_use_case")
        .add_edge("detect_use_case", "search_candidates")
        .add_edge("search_candidates", "score_candidates")
        .add_edge("score_candidates", "summarize")
        .add_edge("summarize", END)
        .compile()
    )


_analysis_graph = None


def get_analysis_graph():
    global _analysis_graph
    if _analysis_graph is None:
        _analysis_graph = build_analysis_graph()
    return _analysis_graph


def analyze_brief(brief: str, num_candidates: int = 8, filters: dict | None = None) -> dict:
    cache_key = make_cache_key(
        "analyze",
        {
            "brief": brief.strip().lower(),
            "num_candidates": num_candidates,
            "filters": filters or {},
        },
    )
    cached = get_cached_query(cache_key, "analyze")
    if cached is not None:
        analysis = dict(cached)
        analysis["analysis_id"] = create_analysis_run(
            brief,
            analysis.get("use_case", "general"),
            "completed",
            result=analysis,
            cache_hit=True,
        )
        return analysis

    result = get_analysis_graph().invoke({
        "brief": brief,
        "num_candidates": num_candidates,
        "filters": filters or {},
        "use_case": "",
        "profile": {},
        "candidates": [],
        "scored_candidates": [],
        "analysis": {},
    })
    analysis = result["analysis"]
    cache_query_result(cache_key, "analyze", analysis)
    analysis["analysis_id"] = create_analysis_run(
        brief,
        analysis.get("use_case", "general"),
        "completed",
        result=analysis,
        cache_hit=False,
    )
    return analysis
