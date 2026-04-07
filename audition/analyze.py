from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from audition.audition import detect_use_case, get_profile, select_candidates
from audition.db import cache_query_result, create_analysis_run, get_cached_query, make_cache_key


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


def _score_candidate(candidate: dict, profile: dict) -> dict:
    traits = candidate.get("traits") or {}
    criteria = profile.get("criteria", [])
    trait_scores = []
    for criterion in criteria:
        mapped = _CRITERIA_TO_TRAITS.get(criterion, [])
        values = [traits.get(name) for name in mapped if traits.get(name) is not None]
        if values:
            trait_scores.append(sum(values) / len(values))

    trait_component = (sum(trait_scores) / len(trait_scores)) if trait_scores else 0.5
    search_component = candidate.get("search_score", 0.0)
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

    total = round((search_component * 0.45) + (trait_component * 0.35) + (cost_component * 0.1) + (latency_component * 0.1), 4)
    rationale = []
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
    scored = [_score_candidate(candidate, state["profile"]) for candidate in state["candidates"]]
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
