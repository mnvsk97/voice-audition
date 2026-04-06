from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

ENRICH_PROMPT = """Listen carefully to this voice sample. Analyze its unique acoustic qualities.

IMPORTANT RULES:
- Description MUST be specific to THIS voice. Never use generic phrases like "youthful and energetic".
- Trait scores MUST vary. No voice scores the same on all traits. Spread values across the 0.0-1.0 range.
- personality_tags describe the speaker's character (e.g. "reassuring", "direct", "playful").
- style_tags describe delivery style (e.g. "conversational", "formal", "measured"). NEVER put accents here.
- use_cases must be complete phrases (e.g. "customer_support", "meditation"), never sentence fragments.
- ALL output must be in English. No other languages.

Respond with ONLY this JSON, no other text:
{"gender": "male or female or neutral", "age_group": "young or middle or mature", "accent": "specific accent like american, british, australian, indian", "description": "2 specific sentences: first describe the acoustic quality (pitch, resonance, pace, breathiness), then describe what makes this voice distinctive compared to others", "texture": "one of: smooth, warm, crisp, gravelly, breathy, raspy, rich, thin", "pitch": "one of: low, medium-low, medium, medium-high, high", "warmth": 0.0, "energy": 0.0, "clarity": 0.0, "authority": 0.0, "friendliness": 0.0, "confidence": 0.0, "personality_tags": ["3-5 character words like reassuring, direct, playful, wise, gentle"], "style_tags": ["3-5 delivery words like conversational, formal, animated, soothing, crisp"], "use_cases": ["2-4 from: healthcare, sales, customer_support, education, meditation, finance, audiobook, voicemail, assistant"]}"""

# Two-pass prompt for text-only models (anthropic, bedrock)
ENRICH_TEXT_PROMPT = """You are analyzing a voice based on acoustic features extracted by an audio model.
Given the features below, produce a rich voice profile.

ACOUSTIC FEATURES:
{features}

IMPORTANT RULES:
- Description MUST be specific and vivid. Never use generic phrases like "youthful and energetic".
- Trait scores MUST vary. Spread values across the 0.0-1.0 range based on the features.
- personality_tags describe the speaker's character (e.g. "reassuring", "direct", "playful").
- style_tags describe delivery style (e.g. "conversational", "formal", "measured"). NEVER put accents here.
- ALL output must be in English.

Respond with ONLY this JSON, no other text:
{"description": "2 vivid sentences about this voice", "warmth": 0.0, "energy": 0.0, "clarity": 0.0, "authority": 0.0, "friendliness": 0.0, "confidence": 0.0, "personality_tags": ["3-5 words"], "style_tags": ["3-5 words"], "use_cases": ["2-4 use cases"]}"""


def _read_audio_b64(audio_path: Path) -> tuple[str, str]:
    """Read audio file and return (base64_data, format)."""
    audio_bytes = audio_path.read_bytes()
    b64 = base64.b64encode(audio_bytes).decode()
    ext = audio_path.suffix.lstrip(".")
    fmt = ext if ext in ("wav", "mp3") else "wav"
    return b64, fmt


# ---------------------------------------------------------------------------
# OpenAI (gpt-4o with audio input)
# ---------------------------------------------------------------------------

def enrich_openai(audio_path: Path, config: dict) -> dict | None:
    import httpx

    api_key = config["api_key"]
    base_url = config.get("base_url", "https://api.openai.com/v1").rstrip("/")
    model = config.get("model", "gpt-4o")

    b64, fmt = _read_audio_b64(audio_path)

    resp = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": ENRICH_PROMPT},
                    {"type": "input_audio", "input_audio": {"data": b64, "format": fmt}},
                ],
            }],
            "max_tokens": 512,
            "temperature": 0.1,
        },
        timeout=60,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"].strip()
    return parse_response(raw)


# ---------------------------------------------------------------------------
# Gemini (native audio input)
# ---------------------------------------------------------------------------

def enrich_gemini(audio_path: Path, config: dict) -> dict | None:
    import httpx

    model = config.get("model", "gemini-2.0-flash")
    credentials_file = config.get("credentials_file")

    if credentials_file:
        api_key = _get_gemini_token_from_sa(str(Path(credentials_file).expanduser()))
        base_url = "https://generativelanguage.googleapis.com/v1beta"
        auth_header = {"Authorization": f"Bearer {api_key}"}
        url = f"{base_url}/models/{model}:generateContent"
    else:
        api_key = config["api_key"]
        base_url = "https://generativelanguage.googleapis.com/v1beta"
        auth_header = {}
        url = f"{base_url}/models/{model}:generateContent?key={api_key}"

    b64, fmt = _read_audio_b64(audio_path)
    mime = {"wav": "audio/wav", "mp3": "audio/mpeg"}.get(fmt, "audio/wav")

    resp = httpx.post(
        url,
        headers={**auth_header, "Content-Type": "application/json"},
        json={
            "contents": [{
                "parts": [
                    {"text": ENRICH_PROMPT},
                    {"inline_data": {"mime_type": mime, "data": b64}},
                ]
            }],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    return parse_response(raw)


def _get_gemini_token_from_sa(credentials_file: str) -> str:
    """Get access token from service account credentials."""
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=["https://www.googleapis.com/auth/generative-language"],
    )
    creds.refresh(Request())
    return creds.token


# ---------------------------------------------------------------------------
# Ollama (local, supports qwen2-audio and other multimodal models)
# ---------------------------------------------------------------------------

def enrich_ollama(audio_path: Path, config: dict) -> dict | None:
    import httpx

    base_url = config.get("base_url", "http://localhost:11434").rstrip("/")
    model = config.get("model", "qwen2-audio")

    b64, _ = _read_audio_b64(audio_path)

    resp = httpx.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": [{
                "role": "user",
                "content": ENRICH_PROMPT,
                "images": [b64],  # Ollama uses 'images' for all binary inputs
            }],
            "stream": False,
            "options": {"temperature": 0.1},
        },
        timeout=120,
    )
    resp.raise_for_status()
    raw = resp.json()["message"]["content"].strip()
    return parse_response(raw)


# ---------------------------------------------------------------------------
# MLX (local Apple Silicon, Qwen2-Audio)
# ---------------------------------------------------------------------------

_mlx_model = None
_mlx_model_name = None


def enrich_mlx(audio_path: Path, config: dict) -> dict | None:
    global _mlx_model, _mlx_model_name

    model_id = config.get("model_id", "mlx-community/Qwen2-Audio-7B-Instruct-4bit")

    if _mlx_model is None or _mlx_model_name != model_id:
        from mlx_audio.stt.utils import load_model
        print(f"[enrich] Loading MLX model {model_id}...")
        _mlx_model = load_model(model_id)
        _mlx_model_name = model_id
        print("[enrich] Model loaded.")

    result = _mlx_model.generate(
        str(audio_path),
        prompt=ENRICH_PROMPT,
        max_tokens=512,
        temperature=0.1,
    )
    raw = result.text.strip()
    return parse_response(raw)


# ---------------------------------------------------------------------------
# Anthropic (two-pass: MLX acoustics → Claude text enrichment)
# ---------------------------------------------------------------------------

def enrich_anthropic(audio_path: Path, config: dict) -> dict | None:
    import httpx

    features = _extract_acoustic_features(audio_path)
    if features is None:
        return None

    api_key = config["api_key"]
    model = config.get("model", "claude-sonnet-4-6")
    prompt = ENRICH_TEXT_PROMPT.format(features=json.dumps(features, indent=2))

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 512,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    raw = resp.json()["content"][0]["text"].strip()
    result = parse_response(raw)
    if result:
        # Merge acoustic features (gender, age, accent, pitch, texture) from local model
        result["gender"] = features.get("gender", result.get("gender", "unknown"))
        result["age_group"] = features.get("age_group", result.get("age_group", "unknown"))
        result["accent"] = features.get("accent", result.get("accent"))
        result["pitch"] = features.get("pitch", result.get("pitch"))
        result["texture"] = features.get("texture", result.get("texture"))
    return result


# ---------------------------------------------------------------------------
# Bedrock (two-pass: MLX acoustics → Claude on Bedrock)
# ---------------------------------------------------------------------------

def enrich_bedrock(audio_path: Path, config: dict) -> dict | None:
    import httpx

    features = _extract_acoustic_features(audio_path)
    if features is None:
        return None

    region = config["region"]
    access_key = config["access_key_id"]
    secret_key = config["secret_access_key"]
    session_token = config.get("session_token")
    model = config.get("model", "anthropic.claude-sonnet-4-6")
    prompt = ENRICH_TEXT_PROMPT.format(features=json.dumps(features, indent=2))

    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 required for Bedrock. Install with: pip install boto3")

    session_kwargs = {
        "region_name": region,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
    }
    if session_token:
        session_kwargs["aws_session_token"] = session_token

    client = boto3.Session(**session_kwargs).client("bedrock-runtime")
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": prompt}],
    })
    resp = client.invoke_model(modelId=model, body=body, contentType="application/json")
    data = json.loads(resp["body"].read())
    raw = data["content"][0]["text"].strip()
    result = parse_response(raw)
    if result:
        result["gender"] = features.get("gender", result.get("gender", "unknown"))
        result["age_group"] = features.get("age_group", result.get("age_group", "unknown"))
        result["accent"] = features.get("accent", result.get("accent"))
        result["pitch"] = features.get("pitch", result.get("pitch"))
        result["texture"] = features.get("texture", result.get("texture"))
    return result


def _extract_acoustic_features(audio_path: Path) -> dict | None:
    """Extract basic acoustic features using Ollama or MLX (local, free)."""
    # Try Ollama first (more portable), fall back to MLX
    quick_prompt = (
        "Listen to this voice. Reply with ONLY this JSON:\n"
        '{"gender":"male/female","age_group":"young/middle/mature",'
        '"accent":"american/british/etc","pitch":"low/medium-low/medium/medium-high/high",'
        '"texture":"smooth/warm/crisp/gravelly/breathy/raspy/rich/thin"}'
    )
    try:
        import httpx
        b64, _ = _read_audio_b64(audio_path)
        resp = httpx.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen2-audio",
                "messages": [{"role": "user", "content": quick_prompt, "images": [b64]}],
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=60,
        )
        if resp.status_code == 200:
            raw = resp.json()["message"]["content"].strip()
            return parse_response(raw)
    except Exception:
        pass

    # Fall back to MLX
    try:
        result = enrich_mlx(audio_path, {"model_id": "mlx-community/Qwen2-Audio-7B-Instruct-4bit"})
        if result:
            return {k: result[k] for k in ("gender", "age_group", "accent", "pitch", "texture") if k in result}
    except Exception:
        pass

    print("[enrich] WARNING: Could not extract acoustic features for two-pass enrichment.")
    print("[enrich] Install Ollama with qwen2-audio, or mlx-audio for Apple Silicon.")
    return None


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "openai": enrich_openai,
    "gemini": enrich_gemini,
    "ollama": enrich_ollama,
    "mlx": enrich_mlx,
    "anthropic": enrich_anthropic,
    "bedrock": enrich_bedrock,
}


def enrich_voice(audio_path: Path, provider: str, provider_config: dict) -> dict | None:
    """Main entry point: enrich a voice from audio using the configured provider."""
    fn = _PROVIDERS.get(provider)
    if fn is None:
        raise ValueError(f"Unknown provider: '{provider}'. Choose from: {', '.join(_PROVIDERS)}")
    return fn(audio_path, provider_config)


# ---------------------------------------------------------------------------
# Response parsing & normalization (shared across all providers)
# ---------------------------------------------------------------------------

def parse_response(raw: str) -> dict | None:
    if '\\"' in raw and '{"' not in raw:
        raw = raw.replace('\\"', '"')

    json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if not json_match:
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
                    json_match = raw[start:i + 1]
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
    def clamp(v):
        if v is None:
            return None
        try:
            f = float(v)
            return max(0.0, min(1.0, round(f, 2)))
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
        "accent": _clean_text(str(data.get("accent", "")).lower().strip()) or None,
        "description": _clean_text(str(data.get("description", "")).strip()) or None,
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
        "style_tags": _clean_style_tags(_to_list(data.get("style_tags"))),
        "use_cases": _to_list(data.get("use_cases")),
    }


def _to_list(val) -> list[str]:
    if isinstance(val, list):
        items = [str(v).strip().lower() for v in val if v]
    elif isinstance(val, str):
        items = [v.strip().lower() for v in val.split(",") if v.strip()]
    else:
        return []
    return [i for i in items if _is_valid_tag(i)]


def _clean_text(text: str) -> str:
    """Strip non-ASCII characters (CJK leaks from multilingual models)."""
    return "".join(c for c in text if c.isascii()).strip()


_ACCENT_WORDS = {"accent", "american", "british", "australian", "indian", "irish", "scottish", "southern", "midwestern", "european"}


def _clean_style_tags(tags: list[str]) -> list[str]:
    return [t for t in tags if not any(w in _ACCENT_WORDS for w in t.split())]


def _is_valid_tag(tag: str) -> bool:
    if not tag or len(tag) < 2:
        return False
    if not tag.isascii():
        return False
    first_word = tag.split()[0] if tag.split() else ""
    if first_word in ("and", "or", "but", "the", "a", "an"):
        return False
    if tag.endswith(".") and " " in tag:
        return False
    return True


def _parse_freetext(raw: str) -> dict | None:
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
        "description": _clean_text(raw[:300]),
        "texture": None,
        "pitch": None,
        "traits": {},
        "personality_tags": [],
        "style_tags": [],
        "use_cases": [],
    }
