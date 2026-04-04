"""Voice classifier using Qwen2-Audio via MLX.

Listens to an audio sample and returns structured voice metadata:
gender, age, accent, description, traits, tags, use cases.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CLASSIFY_PROMPT = """You are a professional voice casting director evaluating a voice for AI voice agent applications. Listen to this voice sample carefully and analyze it across multiple dimensions.

Think about:
- WHO does this voice sound like? What gender, age range, and cultural background?
- HOW does this voice FEEL? Is it warm or cold? Calm or energetic? Friendly or distant?
- WHAT is the vocal texture? Smooth and polished? Gravelly and rough? Breathy and intimate?
- WHERE would this voice work best? Customer service? Healthcare? Sales? Education?
- Think about the speaking pace, pitch level, and how much emotion the voice conveys.

Rate traits on a 0.0-1.0 scale where:
- 0.0-0.2 = very low (e.g., very cold, very monotone, very quiet)
- 0.3-0.4 = somewhat low
- 0.5 = moderate/neutral
- 0.6-0.7 = somewhat high
- 0.8-1.0 = very high (e.g., very warm, very energetic, very clear)

Respond ONLY with a JSON object, no other text:

{
  "gender": "male" or "female" or "neutral",
  "age_group": "young" (18-30) or "middle" (30-50) or "mature" (50+),
  "accent": the accent you hear (e.g., "american", "british", "southern_american", "indian"),
  "description": "2-3 sentences describing how this voice sounds and what personality it projects. Be specific about tone, warmth, and character. Example: 'A warm, gentle female voice with a Southern lilt. Sounds like a trusted friend — calm, patient, and genuinely caring. Would make anxious callers feel immediately at ease.'",
  "texture": one of "smooth", "warm", "crisp", "gravelly", "breathy", "raspy", "rich", "thin",
  "pitch": one of "low", "medium-low", "medium", "medium-high", "high",
  "warmth": 0.0 to 1.0 (cold/clinical to warm/caring),
  "energy": 0.0 to 1.0 (subdued/calm to energetic/upbeat),
  "clarity": 0.0 to 1.0 (mumbled to crisp/articulate),
  "authority": 0.0 to 1.0 (casual/soft to commanding/authoritative),
  "friendliness": 0.0 to 1.0 (distant/formal to approachable/friendly),
  "confidence": 0.0 to 1.0 (hesitant/uncertain to assured/confident),
  "personality_tags": ["3-5 personality words like empathetic, professional, playful, wise, nurturing"],
  "style_tags": ["3-5 acoustic descriptor words like soft, deep, bright, husky, melodic, clear"],
  "use_cases": ["2-4 best use cases like healthcare, customer_support, sales, education, meditation, finance"]
}"""

# Singleton model cache
_model = None
_model_name = None


def _load_model(model_id: str = "mlx-community/Qwen2-Audio-7B-Instruct-4bit"):
    global _model, _model_name
    if _model is not None and _model_name == model_id:
        return _model
    from mlx_audio.stt.utils import load_model
    print(f"[classify] Loading {model_id}...")
    _model = load_model(model_id)
    _model_name = model_id
    print(f"[classify] Model loaded.")
    return _model


def classify_audio(audio_path: Path, model_id: str = "mlx-community/Qwen2-Audio-7B-Instruct-4bit") -> dict | None:
    """Run Qwen2-Audio on an audio file and return structured voice metadata."""
    model = _load_model(model_id)
    result = model.generate(
        str(audio_path),
        prompt=CLASSIFY_PROMPT,
        max_tokens=512,
        temperature=0.1,
    )
    raw = result.text.strip()
    return parse_response(raw)


def parse_response(raw: str) -> dict | None:
    """Parse the model's raw text response into structured voice metadata."""
    # Try to extract JSON from the response
    json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if not json_match:
        # Try harder — maybe there are nested braces
        depth = 0
        start = None
        for i, c in enumerate(raw):
            if c == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    json_match = raw[start:i+1]
                    break
        if isinstance(json_match, str):
            try:
                data = json.loads(json_match)
            except json.JSONDecodeError:
                return _parse_freetext(raw)
        else:
            return _parse_freetext(raw)
    else:
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return _parse_freetext(raw)

    return _normalize(data)


def _normalize(data: dict) -> dict:
    """Normalize parsed JSON into the enrichment format."""
    def clamp(v):
        if v is None:
            return None
        try:
            f = float(v)
            return max(0.0, min(1.0, f))
        except (ValueError, TypeError):
            return None

    gender = str(data.get("gender", "unknown")).lower().strip()
    if gender not in ("male", "female", "neutral"):
        gender = "unknown"

    age = str(data.get("age_group", "unknown")).lower().strip()
    if age not in ("young", "middle", "mature"):
        age = "unknown"

    texture = str(data.get("texture", "")).lower().strip() or None
    valid_textures = {"smooth", "warm", "crisp", "gravelly", "breathy", "raspy", "rich", "thin"}
    if texture and texture not in valid_textures:
        texture = None

    pitch = str(data.get("pitch", "")).lower().strip() or None
    valid_pitches = {"low", "medium-low", "medium", "medium-high", "high"}
    if pitch and pitch not in valid_pitches:
        pitch = None

    return {
        "gender": gender,
        "age_group": age,
        "accent": str(data.get("accent", "")).lower().strip() or None,
        "description": str(data.get("description", "")).strip() or None,
        "texture": texture,
        "pitch": pitch,
        "traits": {
            "warmth": clamp(data.get("warmth")),
            "energy": clamp(data.get("energy")),
            "clarity": clamp(data.get("clarity")),
            "authority": clamp(data.get("authority")),
            "friendliness": clamp(data.get("friendliness")),
            "confidence": clamp(data.get("confidence")),
        },
        "personality_tags": _to_list(data.get("personality_tags")),
        "style_tags": _to_list(data.get("style_tags")),
        "use_cases": _to_list(data.get("use_cases")),
    }


def _to_list(val) -> list[str]:
    if isinstance(val, list):
        return [str(v).strip().lower() for v in val if v]
    if isinstance(val, str):
        return [v.strip().lower() for v in val.split(",") if v.strip()]
    return []


def _parse_freetext(raw: str) -> dict | None:
    """Fallback: extract what we can from free-text response."""
    if not raw or len(raw) < 10:
        return None

    lower = raw.lower()

    gender = "unknown"
    if "female" in lower:
        gender = "female"
    elif "male" in lower and "female" not in lower:
        gender = "male"

    age = "unknown"
    if "young" in lower:
        age = "young"
    elif "mature" in lower or "older" in lower or "senior" in lower:
        age = "mature"
    elif "middle" in lower:
        age = "middle"

    return {
        "gender": gender,
        "age_group": age,
        "accent": None,
        "description": raw[:300].strip(),
        "texture": None,
        "pitch": None,
        "traits": {},
        "personality_tags": [],
        "style_tags": [],
        "use_cases": [],
    }
