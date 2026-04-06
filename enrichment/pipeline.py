from __future__ import annotations

import base64
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import sys

import httpx

from enrichment import CATALOG_DIR


def _log(msg: str):
    print(msg)
    sys.stdout.flush()

SAMPLE_TEXT = (
    "Hi there, welcome back. I wanted to check in and see how you're doing today. "
    "Let me know if there's anything I can help with."
)

MAX_ATTEMPTS = 3
BASE_DELAY = 1.0  # seconds, doubles each retry


# ---------------------------------------------------------------------------
# Audio sample generation
# ---------------------------------------------------------------------------

RIME_LANG_SAMPLES = {
    "eng": SAMPLE_TEXT,
    "spa": "Hola, bienvenido de nuevo. Quería saber cómo estás hoy. Dime si hay algo en lo que pueda ayudarte.",
    "fra": "Bonjour, bon retour. Je voulais prendre de vos nouvelles. Dites-moi si je peux vous aider.",
    "ger": "Hallo, willkommen zurück. Ich wollte nachfragen, wie es Ihnen heute geht. Lassen Sie mich wissen, ob ich helfen kann.",
}


_RIME_STREAMING_MODELS = {"arcana", "mistv3"}  # return raw audio with Accept header
_RIME_JSON_MODELS = {"mist", "mistv2"}          # return base64 JSON with audioContent


def _generate_rime(voice_id: str, model: str, lang: str, out_dir: Path, client: httpx.Client) -> Path | None:
    api_key = os.environ.get("RIME_API_KEY", "")
    if not api_key:
        return None
    text = RIME_LANG_SAMPLES.get(lang, SAMPLE_TEXT)
    body: dict = {"text": text, "speaker": voice_id, "modelId": model}
    if lang != "eng":
        body["lang"] = lang

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if model in _RIME_STREAMING_MODELS:
        headers["Accept"] = "audio/wav"
        resp = client.post("https://users.rime.ai/v1/rime-tts", headers=headers, json=body)
        resp.raise_for_status()
        audio_bytes = resp.content
    else:
        resp = client.post("https://users.rime.ai/v1/rime-tts", headers=headers, json=body)
        resp.raise_for_status()
        audio_bytes = base64.b64decode(resp.json()["audioContent"])

    path = out_dir / f"rime_{voice_id}.wav"
    path.write_bytes(audio_bytes)
    return path


def _generate_elevenlabs(voice_id: str, out_dir: Path, client: httpx.Client) -> Path | None:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        return None
    resp = client.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key},
        json={"text": SAMPLE_TEXT},
    )
    resp.raise_for_status()
    path = out_dir / f"elevenlabs_{voice_id}.mp3"
    path.write_bytes(resp.content)
    return path


def _generate_deepgram(voice_id: str, out_dir: Path, client: httpx.Client) -> Path | None:
    api_key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not api_key:
        return None
    resp = client.post(
        f"https://api.deepgram.com/v1/speak?model={voice_id}",
        headers={"Authorization": f"Token {api_key}"},
        content=SAMPLE_TEXT,
    )
    resp.raise_for_status()
    path = out_dir / f"deepgram_{voice_id}.mp3"
    path.write_bytes(resp.content)
    return path


def _generate_kokoro(voice_id: str, out_dir: Path) -> Path | None:
    """Generate audio sample using the kokoro-onnx package (local, CPU)."""
    try:
        from kokoro_onnx import Kokoro
    except ImportError:
        return None
    try:
        tts = Kokoro("kokoro-v0_19.onnx", "voices.bin")
        samples, sr = tts.create(SAMPLE_TEXT, voice=voice_id, speed=1.0)
        import soundfile as sf
        path = out_dir / f"kokoro_{voice_id}.wav"
        sf.write(str(path), samples, sr)
        return path
    except Exception:
        return None


def _generate_piper(voice_id: str, out_dir: Path) -> Path | None:
    """Generate audio sample using the piper CLI tool (local, CPU)."""
    import shutil
    import subprocess
    if not shutil.which("piper"):
        return None
    path = out_dir / f"piper_{voice_id.replace('/', '_')}.wav"
    try:
        proc = subprocess.run(
            ["piper", "--model", voice_id, "--output_file", str(path)],
            input=SAMPLE_TEXT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode == 0 and path.exists() and path.stat().st_size > 0:
            return path
    except Exception:
        pass
    return None


def _generate_opensource_stub(voice: dict, out_dir: Path, client: httpx.Client) -> None:
    """Stub for open source models that can't easily generate locally.

    Returns None so generate_sample() falls through to preview_url download.
    Orpheus (3B, GPU), Chatterbox (voice cloning), and Fish Speech (voice cloning)
    require hardware or reference audio we can't assume are available.
    """
    return None


_GENERATORS = {
    "rime": lambda v, d, c: _generate_rime(v["provider_voice_id"].split(":")[-1], v.get("provider_model", "mist"), v.get("provider_metadata", {}).get("original_lang_code", "eng"), d, c),
    "elevenlabs": lambda v, d, c: _generate_elevenlabs(v["provider_voice_id"], d, c),
    "deepgram": lambda v, d, c: _generate_deepgram(v["provider_voice_id"], d, c),
    "kokoro": lambda v, d, c: _generate_kokoro(v["provider_voice_id"], d),
    "piper": lambda v, d, c: _generate_piper(v["provider_voice_id"], d),
    "orpheus": _generate_opensource_stub,
    "chatterbox": _generate_opensource_stub,
    "fish-speech": _generate_opensource_stub,
}


def _download_preview(voice: dict, out_dir: Path, client: httpx.Client) -> Path | None:
    url = voice.get("preview_url")
    if not url:
        return None
    try:
        resp = client.get(url)
        resp.raise_for_status()
        ext = ".mp3" if ".mp3" in url else ".wav"
        path = out_dir / f"preview_{voice['id'].replace(':', '_')}{ext}"
        path.write_bytes(resp.content)
        return path
    except Exception:
        return None


def generate_sample(voice: dict, out_dir: Path, client: httpx.Client) -> tuple[Path | None, str | None]:
    """Returns (audio_path, error_reason). One of them is always None."""
    gen = _GENERATORS.get(voice["provider"])
    if gen is not None:
        try:
            result = gen(voice, out_dir, client)
            if result is not None:
                return result, None
        except httpx.HTTPStatusError as e:
            reason = f"http_{e.response.status_code}"
            preview = _download_preview(voice, out_dir, client)
            if preview:
                return preview, None
            return None, reason
        except Exception as e:
            preview = _download_preview(voice, out_dir, client)
            if preview:
                return preview, None
            return None, str(e)[:80]
    preview = _download_preview(voice, out_dir, client)
    if preview:
        return preview, None
    return None, "no_audio_source"


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def _needs_enrichment(voice: dict, retry: bool = False) -> bool:
    status = voice.get("enrichment_status")
    if status == "completed":
        return False
    if status and status.startswith("failed:"):
        if not retry:
            return False
        return voice.get("enrichment_attempts", 0) < MAX_ATTEMPTS
    return True


def _set_status(voice: dict, status: str, reason: str | None = None) -> dict:
    voice = {**voice}
    if reason:
        voice["enrichment_status"] = f"{status}:{reason}"
    else:
        voice["enrichment_status"] = status
    voice["enrichment_attempts"] = voice.get("enrichment_attempts", 0) + 1
    return voice


# ---------------------------------------------------------------------------
# Validation & merge
# ---------------------------------------------------------------------------

def validate_enrichment(enrichment: dict, config: dict | None = None) -> list[str]:
    warnings = []
    min_spread = 0.15
    generic_phrases = ["youthful and energetic", "clear and professional", "warm and friendly tone"]

    if config and "validation" in config:
        v = config["validation"]
        min_spread = v.get("min_trait_spread", min_spread)
        generic_phrases = v.get("generic_phrases", generic_phrases)

    traits = enrichment.get("traits", {})
    values = [v for v in traits.values() if v is not None]
    if len(values) >= 4:
        spread = max(values) - min(values)
        if spread < min_spread:
            warnings.append(f"flat_traits (spread={spread:.2f})")

    desc = (enrichment.get("description") or "").lower()
    for phrase in generic_phrases:
        if phrase in desc:
            warnings.append(f"generic_description ({phrase})")
    return warnings


def merge_enrichment(voice: dict, enrichment: dict) -> dict:
    voice = {**voice}
    for key in ("gender", "age_group", "accent", "description", "texture", "pitch"):
        if enrichment.get(key):
            voice[key] = enrichment[key]
    if "traits" in enrichment:
        merged = {**(voice.get("traits") or {})}
        for k, v in enrichment["traits"].items():
            if v is not None:
                merged[k] = v
        voice["traits"] = merged
    for key in ("personality_tags", "style_tags", "use_cases"):
        if enrichment.get(key):
            voice[key] = sorted(set(voice.get(key, [])) | set(enrichment[key]))
    if "enrichment" in enrichment:
        voice["enrichment"] = enrichment["enrichment"]
    voice["metadata_source"] = "enriched_local"
    voice["enrichment_status"] = "completed"
    voice["last_verified"] = datetime.now(timezone.utc).isoformat()
    return voice


def load_catalog(provider: str) -> list[dict] | None:
    path = CATALOG_DIR / f"{provider}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return data if isinstance(data, list) else data.get("voices", [])


def save_catalog(provider: str, voices: list[dict]) -> None:
    path = CATALOG_DIR / f"{provider}.json"
    path.write_text(json.dumps(voices, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_enrich(catalog_providers: list[str] | None = None, retry: bool = False):
    from enrichment.config import load_config, get_provider_config, validate_credentials
    from enrichment.classify import enrich_voice

    config = load_config()
    enrich_provider, provider_config = get_provider_config(config)

    _log(f"[enrich] Provider: {enrich_provider}")
    _log(f"[enrich] Model: {provider_config.get('model') or provider_config.get('model_id', 'default')}")
    validate_credentials(enrich_provider, provider_config)
    _log(f"[enrich] Credentials OK.{' (retry mode)' if retry else ''}")

    skip = {"providers", "hosting"}
    available = [p.stem for p in CATALOG_DIR.glob("*.json") if p.stem not in skip]
    targets = catalog_providers if catalog_providers else available
    targets = [p for p in targets if p in available]

    if not targets:
        print("[enrich] No catalog files found. Run sync first.")
        return

    model_name = provider_config.get("model") or provider_config.get("model_id", enrich_provider)
    total = 0
    enriched = 0
    skipped = 0
    failed = 0

    with tempfile.TemporaryDirectory(prefix="voice_enrich_") as tmp:
        out_dir = Path(tmp)

        for cat_provider in targets:
            voices = load_catalog(cat_provider)
            if voices is None:
                continue

            pending = [(i, v) for i, v in enumerate(voices) if _needs_enrichment(v, retry=retry)]
            if not pending:
                _log(f"[enrich] {cat_provider}: nothing to enrich")
                continue

            total += len(pending)
            _log(f"[enrich] {cat_provider}: {len(pending)} voices to enrich")

            # Phase 1: Generate all samples (skip model families with 5+ consecutive failures)
            samples: list[tuple[int, dict, Path]] = []
            model_failures: dict[str, int] = {}
            gen_count = 0
            with httpx.Client(timeout=15) as client:
                for idx, voice in pending:
                    gen_count += 1
                    if gen_count % 50 == 0:
                        _log(f"[enrich] {cat_provider}: generating samples... {gen_count}/{len(pending)}")
                    model_key = f"{voice.get('provider')}:{voice.get('provider_model', '')}"
                    if model_failures.get(model_key, 0) >= 5:
                        voices[idx] = _set_status(voice, "failed", "model_unavailable")
                        failed += 1
                        skipped += 1
                        continue

                    audio_path, err = generate_sample(voice, out_dir, client)
                    if audio_path:
                        samples.append((idx, voice, audio_path))
                        model_failures[model_key] = 0
                    else:
                        voices[idx] = _set_status(voice, "failed", err)
                        failed += 1
                        model_failures[model_key] = model_failures.get(model_key, 0) + 1

            gen_failed = len(pending) - len(samples)
            _log(f"[enrich] {cat_provider}: {len(samples)} samples ready, {gen_failed} failed audio gen")
            if gen_failed > 0:
                save_catalog(cat_provider, voices)

            # Phase 2: Enrich with backoff
            dirty = len(pending) - len(samples) > 0  # already have status changes from failed audio
            consecutive_errors = 0

            for idx, voice, audio_path in samples:
                vid = voice.get("id", "?")

                # Backoff on consecutive errors
                if consecutive_errors > 0:
                    delay = min(BASE_DELAY * (2 ** (consecutive_errors - 1)), 30)
                    _log(f"[enrich] Backing off {delay:.0f}s...")
                    time.sleep(delay)

                try:
                    result = enrich_voice(audio_path, enrich_provider, provider_config)
                except Exception as e:
                    _log(f"[enrich] Failed {vid}: {e}")
                    voices[idx] = _set_status(voice, "failed", str(e)[:60])
                    failed += 1
                    consecutive_errors += 1
                    dirty = True
                    # Save progress every 10 failures
                    if failed % 10 == 0:
                        save_catalog(cat_provider, voices)
                    continue

                if result is None:
                    voices[idx] = _set_status(voice, "failed", "empty_result")
                    failed += 1
                    consecutive_errors += 1
                    dirty = True
                    continue

                # Success — reset backoff
                consecutive_errors = 0

                warnings = validate_enrichment(result, config)
                if warnings:
                    _log(f"[enrich] WARNING {vid}: {', '.join(warnings)}")

                result["enrichment"] = {
                    "provider": enrich_provider,
                    "model": model_name,
                    "confidence": 0.5 if warnings else 0.7,
                    "sample_text": SAMPLE_TEXT,
                    "warnings": warnings or None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                voices[idx] = merge_enrichment(voice, result)
                enriched += 1
                dirty = True

                # Save progress every 25 voices
                if enriched % 25 == 0:
                    save_catalog(cat_provider, voices)
                    _log(f"[enrich] Progress: {enriched} enriched, {failed} failed")

            if dirty:
                save_catalog(cat_provider, voices)

    # Summary
    completed = sum(1 for p in targets for v in (load_catalog(p) or []) if v.get("enrichment_status") == "completed")
    failed_total = sum(1 for p in targets for v in (load_catalog(p) or []) if (v.get("enrichment_status") or "").startswith("failed:"))
    pending_total = sum(1 for p in targets for v in (load_catalog(p) or []) if not v.get("enrichment_status"))

    print(f"\n[enrich] This run: +{enriched} enriched, {failed} failed")
    _log(f"[enrich] Overall: {completed} completed, {failed_total} failed, {pending_total} pending")

    if enriched > 0:
        print("[enrich] Rebuilding search index...")
        try:
            from audition.index import run_index
            run_index()
        except Exception as e:
            _log(f"[enrich] Index rebuild failed: {e}")
