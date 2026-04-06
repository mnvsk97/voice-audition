from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

from audition.schema import (
    GENDERS, AGE_GROUPS, TEXTURES, PITCHES, TRAITS,
    USE_CASES, PERSONALITY_TAGS, STYLE_TAGS,
)

_ALLOWED = f"""ALLOWED VALUES (use ONLY these):
- gender: {', '.join(sorted(GENDERS - {'unknown'}))}
- age_group: {', '.join(sorted(AGE_GROUPS - {'unknown'}))}
- texture: {', '.join(sorted(TEXTURES))}
- pitch: {', '.join(sorted(PITCHES))}
- use_cases: {', '.join(sorted(USE_CASES))}
- personality_tags: {', '.join(sorted(PERSONALITY_TAGS))}
- style_tags: {', '.join(sorted(STYLE_TAGS))}"""

ENRICH_PROMPT = f"""Analyze this voice sample's acoustic qualities. Be specific to THIS voice.

Rules: trait scores MUST vary (0.0-1.0), use ALL fitting use_cases, English only.

{_ALLOWED}

Respond with ONLY JSON:
{{"gender": "", "age_group": "", "accent": "e.g. american/british/indian", "description": "2 sentences: acoustic quality, then what's distinctive", "texture": "", "pitch": "", "warmth": 0.0, "energy": 0.0, "clarity": 0.0, "authority": 0.0, "friendliness": 0.0, "confidence": 0.0, "personality_tags": [], "style_tags": [], "use_cases": []}}"""

ENRICH_TEXT_PROMPT = f"""Produce a voice profile from these acoustic features. Be specific.

ACOUSTIC FEATURES:
{{features}}

Rules: trait scores MUST vary (0.0-1.0), use ALL fitting use_cases, English only.

{_ALLOWED}

Respond with ONLY JSON:
{{"description": "2 vivid sentences", "texture": "", "pitch": "", "warmth": 0.0, "energy": 0.0, "clarity": 0.0, "authority": 0.0, "friendliness": 0.0, "confidence": 0.0, "personality_tags": [], "style_tags": [], "use_cases": []}}"""


def _read_audio_b64(audio_path: Path) -> tuple[str, str]:
    audio_bytes = audio_path.read_bytes()
    b64 = base64.b64encode(audio_bytes).decode()
    fmt = audio_path.suffix.lstrip(".")
    return b64, fmt if fmt in ("wav", "mp3") else "wav"


def enrich_openai(audio_path: Path, config: dict) -> dict | None:
    import httpx
    b64, fmt = _read_audio_b64(audio_path)
    resp = httpx.post(
        f"{config.get('base_url', 'https://api.openai.com/v1').rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {config['api_key']}"},
        json={
            "model": config.get("model", "gpt-4o"),
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": ENRICH_PROMPT},
                {"type": "input_audio", "input_audio": {"data": b64, "format": fmt}},
            ]}],
            "max_tokens": 512, "temperature": 0.1,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return parse_response(resp.json()["choices"][0]["message"]["content"].strip())


def enrich_gemini(audio_path: Path, config: dict) -> dict | None:
    import httpx
    model = config.get("model", "gemini-2.0-flash")
    creds = config.get("credentials_file")
    if creds:
        token = _get_gemini_token_from_sa(str(Path(creds).expanduser()))
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={config['api_key']}"
        headers = {"Content-Type": "application/json"}

    b64, fmt = _read_audio_b64(audio_path)
    mime = {"wav": "audio/wav", "mp3": "audio/mpeg"}.get(fmt, "audio/wav")
    resp = httpx.post(url, headers=headers, json={
        "contents": [{"parts": [
            {"text": ENRICH_PROMPT},
            {"inline_data": {"mime_type": mime, "data": b64}},
        ]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
    }, timeout=60)
    resp.raise_for_status()
    return parse_response(resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip())


def _get_gemini_token_from_sa(credentials_file: str) -> str:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_file(
        credentials_file, scopes=["https://www.googleapis.com/auth/generative-language"])
    creds.refresh(Request())
    return creds.token


def enrich_ollama(audio_path: Path, config: dict) -> dict | None:
    import httpx
    b64, _ = _read_audio_b64(audio_path)
    resp = httpx.post(
        f"{config.get('base_url', 'http://localhost:11434').rstrip('/')}/api/chat",
        json={
            "model": config.get("model", "qwen2-audio"),
            "messages": [{"role": "user", "content": ENRICH_PROMPT, "images": [b64]}],
            "stream": False, "options": {"temperature": 0.1},
        },
        timeout=120,
    )
    resp.raise_for_status()
    return parse_response(resp.json()["message"]["content"].strip())


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
    result = _mlx_model.generate(str(audio_path), prompt=ENRICH_PROMPT, max_tokens=512, temperature=0.1)
    return parse_response(result.text.strip())


def _extract_acoustic_features(audio_path: Path) -> dict | None:
    """Extract basic features via Ollama or MLX for two-pass enrichment."""
    quick_prompt = (
        "Listen to this voice. Reply with ONLY JSON:\n"
        '{"gender":"male/female","age_group":"young/middle/mature",'
        '"accent":"american/british/etc","pitch":"low/medium-low/medium/medium-high/high",'
        '"texture":"smooth/warm/crisp/gravelly/breathy/raspy/rich/thin"}'
    )
    try:
        import httpx
        b64, _ = _read_audio_b64(audio_path)
        resp = httpx.post("http://localhost:11434/api/chat", json={
            "model": "qwen2-audio",
            "messages": [{"role": "user", "content": quick_prompt, "images": [b64]}],
            "stream": False, "options": {"temperature": 0.1},
        }, timeout=60)
        if resp.status_code == 200:
            return parse_response(resp.json()["message"]["content"].strip())
    except Exception:
        pass
    try:
        result = enrich_mlx(audio_path, {"model_id": "mlx-community/Qwen2-Audio-7B-Instruct-4bit"})
        if result:
            return {k: result[k] for k in ("gender", "age_group", "accent", "pitch", "texture") if k in result}
    except Exception:
        pass
    print("[enrich] WARNING: No local audio model available for two-pass enrichment.")
    return None


def _two_pass_enrich(audio_path: Path, config: dict, api_call) -> dict | None:
    """Shared logic for anthropic/bedrock two-pass enrichment."""
    features = _extract_acoustic_features(audio_path)
    if features is None:
        return None
    prompt = ENRICH_TEXT_PROMPT.format(features=json.dumps(features, indent=2))
    result = api_call(prompt, config)
    if result:
        for k in ("gender", "age_group", "accent", "pitch", "texture"):
            if features.get(k):
                result[k] = features[k]
    return result


def enrich_anthropic(audio_path: Path, config: dict) -> dict | None:
    import httpx

    def call(prompt, cfg):
        resp = httpx.post("https://api.anthropic.com/v1/messages", headers={
            "x-api-key": cfg["api_key"], "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }, json={
            "model": cfg.get("model", "claude-sonnet-4-6"),
            "max_tokens": 512, "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
        }, timeout=60)
        resp.raise_for_status()
        return parse_response(resp.json()["content"][0]["text"].strip())

    return _two_pass_enrich(audio_path, config, call)


def enrich_bedrock(audio_path: Path, config: dict) -> dict | None:
    def call(prompt, cfg):
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 required for Bedrock")
        session_kwargs = {
            "region_name": cfg["region"],
            "aws_access_key_id": cfg["access_key_id"],
            "aws_secret_access_key": cfg["secret_access_key"],
        }
        if cfg.get("session_token"):
            session_kwargs["aws_session_token"] = cfg["session_token"]
        client = boto3.Session(**session_kwargs).client("bedrock-runtime")
        resp = client.invoke_model(
            modelId=cfg.get("model", "anthropic.claude-sonnet-4-6"),
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31", "max_tokens": 512,
                "temperature": 0.1, "messages": [{"role": "user", "content": prompt}],
            }),
            contentType="application/json",
        )
        return parse_response(json.loads(resp["body"].read())["content"][0]["text"].strip())

    return _two_pass_enrich(audio_path, config, call)


_PROVIDERS = {
    "openai": enrich_openai, "gemini": enrich_gemini, "ollama": enrich_ollama,
    "mlx": enrich_mlx, "anthropic": enrich_anthropic, "bedrock": enrich_bedrock,
}


def enrich_voice(audio_path: Path, provider: str, provider_config: dict) -> dict | None:
    fn = _PROVIDERS.get(provider)
    if fn is None:
        raise ValueError(f"Unknown provider: '{provider}'. Choose from: {', '.join(_PROVIDERS)}")
    return fn(audio_path, provider_config)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def parse_response(raw: str) -> dict | None:
    if '\\"' in raw and '{"' not in raw:
        raw = raw.replace('\\"', '"')
    # Try simple single-object match first
    m = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if not m:
        # Try nested braces
        depth, start = 0, None
        for i, c in enumerate(raw):
            if c == '{':
                if depth == 0: start = i
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    m = raw[start:i + 1]
                    break
        if isinstance(m, str):
            try:
                return _normalize(json.loads(m))
            except json.JSONDecodeError:
                return _parse_freetext(raw)
        return _parse_freetext(raw)
    try:
        return _normalize(json.loads(m.group()))
    except json.JSONDecodeError:
        return _parse_freetext(raw)


def _normalize(data: dict) -> dict:
    def clamp(v):
        if v is None: return None
        try: return max(0.0, min(1.0, round(float(v), 2)))
        except (ValueError, TypeError): return None

    gender = str(data.get("gender", "unknown")).lower().strip()
    age = str(data.get("age_group", "unknown")).lower().strip()
    texture = str(data.get("texture", "")).lower().strip() or None
    pitch = str(data.get("pitch", "")).lower().strip() or None

    return {
        "gender": gender if gender in GENDERS and gender != "unknown" else "unknown",
        "age_group": age if age in AGE_GROUPS and age != "unknown" else "unknown",
        "accent": _ascii(str(data.get("accent", "")).lower().strip()) or None,
        "description": _ascii(str(data.get("description", "")).strip()) or None,
        "texture": texture if texture in TEXTURES else None,
        "pitch": pitch if pitch in PITCHES else None,
        "traits": {t: clamp(data.get(t)) for t in TRAITS},
        "personality_tags": _filter(data.get("personality_tags"), PERSONALITY_TAGS),
        "style_tags": _filter(data.get("style_tags"), STYLE_TAGS),
        "use_cases": _filter(data.get("use_cases"), USE_CASES),
    }


def _filter(val, allowed: set) -> list[str]:
    if isinstance(val, list):
        items = [str(v).strip().lower().replace(" ", "_") for v in val if v]
    elif isinstance(val, str):
        items = [v.strip().lower().replace(" ", "_") for v in val.split(",") if v.strip()]
    else:
        return []
    return [i for i in items if i in allowed]


def _ascii(text: str) -> str:
    return "".join(c for c in text if c.isascii()).strip()


def _parse_freetext(raw: str) -> dict | None:
    if not raw or len(raw) < 10:
        return None
    lower = raw.lower()
    gender = "female" if "female" in lower else ("male" if "male" in lower else "unknown")
    age = "young" if "young" in lower else ("mature" if "mature" in lower or "older" in lower else ("middle" if "middle" in lower else "unknown"))
    return {
        "gender": gender, "age_group": age, "accent": None,
        "description": _ascii(raw[:300]), "texture": None, "pitch": None,
        "traits": {}, "personality_tags": [], "style_tags": [], "use_cases": [],
    }
