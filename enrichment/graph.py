"""LangGraph enrichment workflow: generate audio -> describe -> score -> validate -> retry."""
from __future__ import annotations

import operator
import re
import json
from pathlib import Path
from typing import Annotated, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, RetryPolicy
from typing_extensions import TypedDict

from audition.schema import (
    GENDERS, AGE_GROUPS, TEXTURES, PITCHES, TRAITS,
    USE_CASES, PERSONALITY_TAGS, STYLE_TAGS,
)

MAX_ATTEMPTS = 3


class EnrichState(TypedDict):
    voice: dict
    audio_path: str | None
    description: str | None
    scores: dict | None
    validation_errors: Annotated[list, operator.add]
    attempt: int
    status: str  # pending | completed | failed


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

DESCRIBE_PROMPT = """Listen to this voice sample. Describe what you hear in 3-4 specific sentences.

Focus on:
- Pitch range and register (high, low, where it sits)
- Resonance and texture (breathy, nasal, chest voice, smooth, raspy)
- Pacing and rhythm (fast, measured, deliberate, natural pauses)
- Energy and emotional tone (warm, detached, enthusiastic, calm)
- What makes this voice DISTINCTIVE compared to a generic voice

Do NOT score anything. Just describe what you hear as specifically as possible.
Be concrete — mention specific acoustic qualities, not vague adjectives."""

DESCRIBE_RETRY_PROMPT = """Listen to this voice sample again. Your previous description had issues:
{feedback}

Write a NEW description (3-4 sentences) that fixes these problems.
Be specific about THIS voice's acoustic qualities. No generic phrases."""


def _score_prompt(description: str) -> str:
    return f"""You previously described this voice as:
"{description}"

Now score it. Use the description above to ground your scores — don't contradict what you wrote.

ALLOWED VALUES (use ONLY these):
- gender: male, female, neutral
- age_group: young, middle, mature
- texture: {', '.join(sorted(TEXTURES))}
- pitch: {', '.join(sorted(PITCHES))}
- use_cases (pick ALL that fit): {', '.join(sorted(USE_CASES))}
- personality_tags (3-5): {', '.join(sorted(PERSONALITY_TAGS))}
- style_tags (3-5): {', '.join(sorted(STYLE_TAGS))}

Score each trait 0.0-1.0. Spread your scores — no voice is the same on everything.

Respond with ONLY JSON:
{{"gender": "", "age_group": "", "accent": "", "texture": "", "pitch": "", "warmth": 0.0, "energy": 0.0, "clarity": 0.0, "authority": 0.0, "friendliness": 0.0, "confidence": 0.0, "personality_tags": [], "style_tags": [], "use_cases": []}}"""


def _score_retry_prompt(description: str, feedback: str) -> str:
    return f"""You described this voice as:
"{description}"

Your previous scoring had issues:
{feedback}

Re-score. Ground your scores in the description. Spread trait values.

ALLOWED VALUES:
- gender: male, female, neutral
- age_group: young, middle, mature
- texture: {', '.join(sorted(TEXTURES))}
- pitch: {', '.join(sorted(PITCHES))}
- use_cases: {', '.join(sorted(USE_CASES))}
- personality_tags: {', '.join(sorted(PERSONALITY_TAGS))}
- style_tags: {', '.join(sorted(STYLE_TAGS))}

Respond with ONLY JSON:
{{"gender": "", "age_group": "", "accent": "", "texture": "", "pitch": "", "warmth": 0.0, "energy": 0.0, "clarity": 0.0, "authority": 0.0, "friendliness": 0.0, "confidence": 0.0, "personality_tags": [], "style_tags": [], "use_cases": []}}"""


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def generate_audio(state: EnrichState) -> dict:
    """Generate TTS audio sample for the voice."""
    import tempfile
    import httpx
    from enrichment.pipeline import generate_sample

    voice = state["voice"]
    with tempfile.TemporaryDirectory(prefix="enrich_") as tmp:
        out_dir = Path(tmp)
        with httpx.Client(timeout=15) as client:
            audio_path, err = generate_sample(voice, out_dir, client)
        if audio_path:
            # Copy to a stable location (tempdir gets cleaned up)
            stable = Path(tempfile.mktemp(suffix=audio_path.suffix, prefix="voice_"))
            stable.write_bytes(audio_path.read_bytes())
            return {"audio_path": str(stable), "status": "pending"}
        return {"audio_path": None, "status": "failed", "validation_errors": [f"audio_gen_failed:{err}"]}


def describe_voice(state: EnrichState) -> dict:
    """LLM listens and produces freeform description (no scoring)."""
    errors = state.get("validation_errors", [])
    feedback_items = [e for e in errors if e.startswith("description:")]

    if feedback_items and state.get("description"):
        feedback = "\n".join(e.split(":", 1)[1] for e in feedback_items)
        prompt = DESCRIBE_RETRY_PROMPT.format(feedback=feedback)
    else:
        prompt = DESCRIBE_PROMPT

    raw = _call_llm(state["audio_path"], prompt)
    if not raw:
        return {"description": None, "status": "failed", "validation_errors": ["llm_call_failed"]}

    # Clean non-ASCII
    description = "".join(c for c in raw if c.isascii()).strip()
    return {"description": description, "attempt": state.get("attempt", 0) + 1}


def score_traits(state: EnrichState) -> dict:
    """LLM scores traits grounded on its own description."""
    description = state["description"]
    if not description:
        return {"scores": None, "status": "failed"}

    errors = state.get("validation_errors", [])
    score_errors = [e for e in errors if e.startswith("scores:")]

    if score_errors and state.get("scores"):
        feedback = "\n".join(e.split(":", 1)[1] for e in score_errors)
        prompt = _score_retry_prompt(description, feedback)
    else:
        prompt = _score_prompt(description)

    raw = _call_llm(state["audio_path"], prompt)
    if not raw:
        return {"scores": None, "status": "failed", "validation_errors": ["score_llm_failed"]}

    scores = _parse_scores(raw)
    if not scores:
        return {"scores": None, "validation_errors": ["scores:Could not parse JSON from response"]}
    return {"scores": scores}


def validate(state: EnrichState) -> Command[Literal["describe_voice", "__end__"]]:
    """Validate enrichment quality. Route to retry or completion."""
    errors = []
    description = state.get("description") or ""
    scores = state.get("scores")
    attempt = state.get("attempt", 0)

    # Validate description
    if len(description) < 30:
        errors.append("description:Too short. Write 3-4 specific sentences about acoustic qualities.")
    generic = ["warm and friendly", "clear and professional", "youthful and energetic",
               "pleasant voice", "natural sounding"]
    for phrase in generic:
        if phrase in description.lower():
            errors.append(f"description:Generic phrase '{phrase}'. Describe specific acoustic qualities instead.")

    # Validate scores
    if scores:
        trait_vals = [scores.get(t) for t in TRAITS if scores.get(t) is not None]
        if len(trait_vals) >= 4:
            spread = max(trait_vals) - min(trait_vals)
            if spread < 0.15:
                errors.append(f"scores:Trait spread is only {spread:.2f}. Differentiate — no voice is the same on everything.")

        if not scores.get("use_cases"):
            errors.append("scores:No use_cases. Pick ALL fitting use cases from the allowed list.")
        if not scores.get("personality_tags"):
            errors.append("scores:No personality_tags. Pick 3-5 from the allowed list.")
    else:
        errors.append("scores:No scores produced.")

    if errors and attempt < MAX_ATTEMPTS:
        return Command(update={"validation_errors": errors, "status": "pending"}, goto="describe_voice")

    if errors:
        return Command(update={"validation_errors": errors, "status": "failed"}, goto=END)

    return Command(update={"status": "completed"}, goto=END)


# ---------------------------------------------------------------------------
# LLM call (uses enrichment config)
# ---------------------------------------------------------------------------

_judge_provider = None
_judge_config = None


def init_llm():
    """Load enrichment config once."""
    global _judge_provider, _judge_config
    if _judge_provider is None:
        from enrichment.config import load_config, get_provider_config, validate_credentials
        config = load_config()
        _judge_provider, _judge_config = get_provider_config(config)
        validate_credentials(_judge_provider, _judge_config)


def _call_llm(audio_path: str | None, prompt: str) -> str | None:
    """Call the configured LLM with audio + prompt. Returns raw text."""
    import base64
    import httpx

    init_llm()
    if not audio_path:
        return None

    audio_bytes = Path(audio_path).read_bytes()
    b64 = base64.b64encode(audio_bytes).decode()
    ext = Path(audio_path).suffix.lstrip(".")
    mime = {"wav": "audio/wav", "mp3": "audio/mpeg"}.get(ext, "audio/wav")

    try:
        if _judge_provider == "gemini":
            return _call_gemini(b64, mime, prompt)
        elif _judge_provider == "openai":
            return _call_openai(b64, ext, prompt)
        elif _judge_provider == "ollama":
            return _call_ollama(b64, prompt)
        elif _judge_provider == "mlx":
            return _call_mlx(audio_path, prompt)
        else:
            return None
    except Exception as e:
        print(f"  [llm] {_judge_provider} error: {e}")
        return None


def _call_gemini(b64: str, mime: str, prompt: str) -> str:
    import httpx
    model = _judge_config.get("model", "gemini-2.0-flash")
    creds = _judge_config.get("credentials_file")
    if creds:
        from enrichment.classify import _get_gemini_token_from_sa
        token = _get_gemini_token_from_sa(str(Path(creds).expanduser()))
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={_judge_config['api_key']}"
        headers = {"Content-Type": "application/json"}
    resp = httpx.post(url, headers=headers, json={
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": b64}}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_openai(b64: str, fmt: str, prompt: str) -> str:
    import httpx
    base_url = _judge_config.get("base_url", "https://api.openai.com/v1").rstrip("/")
    resp = httpx.post(f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {_judge_config['api_key']}"},
        json={"model": _judge_config.get("model", "gpt-4o"),
              "messages": [{"role": "user", "content": [
                  {"type": "text", "text": prompt},
                  {"type": "input_audio", "input_audio": {"data": b64, "format": fmt}},
              ]}], "max_tokens": 512, "temperature": 0.1}, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _call_ollama(b64: str, prompt: str) -> str:
    import httpx
    base_url = _judge_config.get("base_url", "http://localhost:11434").rstrip("/")
    resp = httpx.post(f"{base_url}/api/chat", json={
        "model": _judge_config.get("model", "qwen2-audio"),
        "messages": [{"role": "user", "content": prompt, "images": [b64]}],
        "stream": False, "options": {"temperature": 0.1},
    }, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def _call_mlx(audio_path: str, prompt: str) -> str:
    from enrichment.classify import enrich_mlx, _mlx_model
    import enrichment.classify as cl
    model_id = _judge_config.get("model_id", "mlx-community/Qwen2-Audio-7B-Instruct-4bit")
    if cl._mlx_model is None or cl._mlx_model_name != model_id:
        from mlx_audio.stt.utils import load_model
        cl._mlx_model = load_model(model_id)
        cl._mlx_model_name = model_id
    result = cl._mlx_model.generate(audio_path, prompt=prompt, max_tokens=512, temperature=0.1)
    return result.text.strip()


# ---------------------------------------------------------------------------
# Parse helpers
# ---------------------------------------------------------------------------

def _parse_scores(raw: str) -> dict | None:
    """Parse LLM JSON response into normalized scores dict."""
    from enrichment.classify import _normalize
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
    except json.JSONDecodeError:
        return None
    return _normalize(data)


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------

def build_enrichment_graph() -> StateGraph:
    graph = (
        StateGraph(EnrichState)
        .add_node("generate_audio", generate_audio, retry=RetryPolicy(max_attempts=2))
        .add_node("describe_voice", describe_voice, retry=RetryPolicy(max_attempts=2))
        .add_node("score_traits", score_traits, retry=RetryPolicy(max_attempts=2))
        .add_node("validate", validate)
        .add_edge(START, "generate_audio")
    )

    # generate_audio -> describe_voice if audio OK, else END
    def audio_ok(state: EnrichState) -> Literal["describe_voice", "__end__"]:
        return "describe_voice" if state.get("audio_path") else END

    graph.add_conditional_edges("generate_audio", audio_ok, ["describe_voice", END])
    graph.add_edge("describe_voice", "score_traits")
    graph.add_edge("score_traits", "validate")
    # validate uses Command to route to describe_voice or END

    return graph.compile()


# Singleton
_graph = None


def get_enrichment_graph():
    global _graph
    if _graph is None:
        _graph = build_enrichment_graph()
    return _graph


def enrich_voice_graph(voice: dict) -> dict:
    """Run the enrichment graph for a single voice. Returns final state."""
    init_llm()
    graph = get_enrichment_graph()
    result = graph.invoke({
        "voice": voice,
        "audio_path": None,
        "description": None,
        "scores": None,
        "validation_errors": [],
        "attempt": 0,
        "status": "pending",
    })
    return result
