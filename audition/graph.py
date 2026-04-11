"""LangGraph audition workflow: generate audio -> per-candidate notes (fan-out) -> compare -> rank."""
from __future__ import annotations

import json
import operator
import re
import tempfile
from pathlib import Path
from typing import Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, RetryPolicy
from typing_extensions import TypedDict


class AuditionState(TypedDict):
    brief: str
    use_case: str
    profile: dict                                     # criteria, criteria_labels, scripts
    candidates: list[dict]                            # voices with audio paths per script
    candidate_notes: Annotated[list, operator.add]    # fan-out accumulates here
    comparison: str | None                            # cross-candidate analysis
    scorecard: list[dict]                             # final ranked results


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def _notes_prompt(brief: str, use_case: str, criteria_labels: dict, script: dict) -> str:
    criteria = "\n".join(f"- {k}: {v}" for k, v in criteria_labels.items())
    return f"""You are evaluating a voice for: "{brief}" (category: {use_case}).

This audio is the voice reading: "{script['text']}"
Purpose: {script['purpose']}

Listen carefully and take detailed notes on how this voice performs for this use case.
Address each criterion:
{criteria}

Write 2-3 sentences of specific observations. Note strengths AND weaknesses.
Do NOT score yet — just observe and describe what you hear."""


def _compare_prompt(brief: str, use_case: str, criteria_labels: dict, all_notes: list[dict]) -> str:
    criteria = "\n".join(f"- {k}: {v}" for k, v in criteria_labels.items())
    candidates_text = ""
    for n in all_notes:
        candidates_text += f"\n### {n['name']} ({n['provider']})\n"
        for script_note in n["notes"]:
            candidates_text += f"**{script_note['script']}**: {script_note['text']}\n"

    return f"""You are selecting the best voice for: "{brief}" (category: {use_case}).

CRITERIA:
{criteria}

Here are your observations for each candidate:
{candidates_text}

Now compare ALL candidates against each other. For each criterion, rank the candidates
from best to worst. Then produce a final ranking.

Respond with ONLY JSON:
{{"rankings": [{{"id": "voice_id", "name": "name", "total": 0, "scores": {{{", ".join(f'"{k}": 0' for k in criteria_labels)}}}, "strengths": "brief", "weaknesses": "brief"}}], "recommendation": "1-2 sentences explaining your top pick", "runner_up": "1 sentence on second choice"}}

Score 1-10 per criterion. Rankings should be ordered best-first.
Be decisive — avoid ties. There IS a best voice for this use case."""


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def generate_audio_all(state: AuditionState) -> dict:
    """Generate audio for all candidates across all scripts."""
    import httpx
    from audition.audition import _generate_script_audio

    profile = state["profile"]
    scripts = profile["scripts"]
    candidates = []

    audio_dir = Path(tempfile.mkdtemp(prefix="audition_audio_"))
    with httpx.Client(timeout=30) as client:
        for voice in state["candidates"]:
            audio_files = []
            for script in scripts:
                path, err = _generate_script_audio(voice, script["text"], script["name"], audio_dir, client)
                audio_files.append({
                    "script": script["name"],
                    "path": str(path) if path else None,
                    "error": err,
                })
            ok = sum(1 for a in audio_files if a["path"])
            print(f"  [audio] {voice.get('name', '?')}: {ok}/{len(scripts)} scripts")
            candidates.append({**voice, "_audio": audio_files, "_audio_dir": str(audio_dir)})

    return {"candidates": candidates}


def fan_out_candidates(state: AuditionState) -> list[Send]:
    """Fan out: one worker per candidate to take per-script notes."""
    sends = []
    for candidate in state["candidates"]:
        sends.append(Send("take_notes", {
            "candidate": candidate,
            "brief": state["brief"],
            "use_case": state["use_case"],
            "profile": state["profile"],
        }))
    return sends


def take_notes(state: dict) -> dict:
    """Worker node: LLM listens to all scripts for one candidate, takes notes."""
    from enrichment.graph import _call_llm, init_llm
    init_llm()

    candidate = state["candidate"]
    profile = state["profile"]
    brief = state["brief"]
    use_case = state["use_case"]
    scripts = profile["scripts"]

    notes = []
    for i, script in enumerate(scripts):
        audio_info = candidate.get("_audio", [])[i] if i < len(candidate.get("_audio", [])) else {}
        audio_path = audio_info.get("path")
        if not audio_path:
            notes.append({"script": script["name"], "text": "Audio generation failed."})
            continue

        prompt = _notes_prompt(brief, use_case, profile["criteria_labels"], script)
        raw = _call_llm(audio_path, prompt)
        notes.append({"script": script["name"], "text": raw or "LLM call failed."})

    return {"candidate_notes": [{
        "id": candidate["id"],
        "name": candidate.get("name", "?"),
        "provider": candidate.get("provider", "?"),
        "notes": notes,
    }]}


def compare_all(state: AuditionState) -> dict:
    """LLM sees ALL candidates' notes and produces relative ranking."""
    from enrichment.graph import _call_llm, init_llm
    init_llm()

    # For comparison, we don't need audio — just the notes
    # Use a text-only call if possible, otherwise use any audio as context
    all_notes = state["candidate_notes"]
    profile = state["profile"]

    prompt = _compare_prompt(state["brief"], state["use_case"], profile["criteria_labels"], all_notes)

    # Try to find any audio file to use as context (some providers need it)
    any_audio = None
    for c in state["candidates"]:
        for a in c.get("_audio", []):
            if a.get("path"):
                any_audio = a["path"]
                break
        if any_audio:
            break

    raw = _call_llm(any_audio, prompt)
    return {"comparison": raw}


def rank(state: AuditionState) -> dict:
    """Parse comparison into final scorecard."""
    raw = state.get("comparison") or ""
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        # Fallback: return candidates ordered by search score
        return {"scorecard": [{"id": c["id"], "name": c.get("name"), "provider": c.get("provider"),
                               "total": 0, "scores": {}, "notes": "Comparison failed"}
                              for c in state["candidates"]]}

    try:
        data = json.loads(m.group())
    except json.JSONDecodeError:
        return {"scorecard": []}

    rankings = data.get("rankings", [])
    recommendation = data.get("recommendation", "")
    runner_up = data.get("runner_up", "")

    # Build scorecard with audio file references
    audio_map = {c["id"]: [a["path"] for a in c.get("_audio", []) if a.get("path")]
                 for c in state["candidates"]}

    scorecard = []
    for r in rankings:
        vid = r.get("id", "")
        scorecard.append({
            "id": vid,
            "name": r.get("name", ""),
            "provider": next((c.get("provider") for c in state["candidates"] if c["id"] == vid), ""),
            "total": r.get("total", 0),
            "scores": r.get("scores", {}),
            "strengths": r.get("strengths", ""),
            "weaknesses": r.get("weaknesses", ""),
            "audio_files": audio_map.get(vid, []),
        })

    if scorecard:
        scorecard[0]["recommendation"] = recommendation
    if len(scorecard) > 1:
        scorecard[1]["runner_up"] = runner_up

    return {"scorecard": scorecard}


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------

def build_audition_graph():
    graph = (
        StateGraph(AuditionState)
        .add_node("generate_audio_all", generate_audio_all)
        .add_node("take_notes", take_notes, retry=RetryPolicy(max_attempts=2))
        .add_node("compare_all", compare_all, retry=RetryPolicy(max_attempts=2))
        .add_node("rank", rank)
        .add_edge(START, "generate_audio_all")
        .add_conditional_edges("generate_audio_all", fan_out_candidates, ["take_notes"])
        .add_edge("take_notes", "compare_all")
        .add_edge("compare_all", "rank")
        .add_edge("rank", END)
    )
    return graph.compile()


_graph = None


def get_audition_graph():
    global _graph
    if _graph is None:
        _graph = build_audition_graph()
    return _graph


def run_audition_graph(brief: str, use_case: str, profile: dict, candidates: list[dict]) -> dict:
    """Run the full audition graph. Returns final state with scorecard."""
    from enrichment.graph import init_llm
    init_llm()

    graph = get_audition_graph()
    result = graph.invoke({
        "brief": brief,
        "use_case": use_case,
        "profile": profile,
        "candidates": candidates,
        "candidate_notes": [],
        "comparison": None,
        "scorecard": [],
    })
    return result
