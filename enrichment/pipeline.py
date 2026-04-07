from __future__ import annotations

import base64
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import sys

import click
import httpx

from audition.db import get_provider_record, list_providers, load_voices, record_pipeline_run, upsert_voices


def _log(msg: str):
    print(msg)
    sys.stdout.flush()
SAMPLE_TEXT = (
    "Hi there, welcome back. I wanted to check in and see how you're doing today. "
    "Your account has been upgraded with priority support and faster response times. "
    "If you have any questions, don't hesitate to reach out. I'm here to help."
)

MAX_ATTEMPTS = 3
BASE_DELAY = 1.0  # seconds, doubles each retry


def estimate_rime_enrichment_cost(voice_count: int) -> dict | None:
    rime = get_provider_record("rime") or {}
    pricing = rime.get("pricing", {}) if isinstance(rime, dict) else {}
    rate = pricing.get("estimated_cost_per_minute")
    if not isinstance(rate, (int, float)):
        return None
    return {
        "voice_count": voice_count,
        "unit_cost_usd": float(rate),
        "estimated_cost_usd": round(float(rate) * voice_count, 2),
        "pricing_updated": pricing.get("pricing_updated"),
    }


def preview_enrich_targets(catalog_providers: list[str] | None = None, retry: bool = False,
                           limit: int | None = None) -> dict[str, dict]:
    available = list_providers()
    targets = catalog_providers if catalog_providers else available
    targets = [p for p in targets if p in available]

    preview: dict[str, dict] = {}
    for cat_provider in targets:
        voices = load_catalog(cat_provider)
        if voices is None:
            continue
        pending = [(i, v) for i, v in enumerate(voices) if _needs_enrichment(v, retry=retry)]
        if limit is not None:
            pending = pending[:limit]
        info = {
            "total_count": len(voices),
            "eligible_count": len(pending),
            "limit": limit,
            "estimated_cost_usd": None,
        }
        if cat_provider == "rime" and pending:
            estimate = estimate_rime_enrichment_cost(len(pending))
            if estimate:
                info.update(estimate)
        preview[cat_provider] = info
    return preview


# ---------------------------------------------------------------------------
# Audio sample generation
# ---------------------------------------------------------------------------

RIME_LANG_SAMPLES = {
    "eng": SAMPLE_TEXT,
    "spa": "Hola, bienvenido de nuevo. Tu cuenta ha sido actualizada con soporte prioritario. Si tienes preguntas, no dudes en contactarnos.",
    "fra": "Bonjour, bon retour. Votre compte a été mis à niveau avec un support prioritaire. N'hésitez pas à nous contacter si vous avez des questions.",
    "ger": "Hallo, willkommen zurück. Ihr Konto wurde mit priorisiertem Support aktualisiert. Zögern Sie nicht, uns bei Fragen zu kontaktieren.",
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
    try:
        voices = load_voices(provider=provider)
        return voices if voices else []
    except Exception:
        return None


def save_catalog(provider: str, voices: list[dict]) -> None:
    del provider
    upsert_voices(voices)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_enrich(catalog_providers: list[str] | None = None, retry: bool = False,
               limit: int | None = None, yes: bool = False) -> dict:
    from enrichment.graph import enrich_voice_graph, init_llm

    preview = preview_enrich_targets(catalog_providers, retry=retry, limit=limit)
    if preview:
        print("[enrich] Preflight:")
        for provider, info in preview.items():
            line = f"  {provider}: {info['eligible_count']} voices"
            if info.get("estimated_cost_usd") is not None:
                line += f", est ${info['estimated_cost_usd']:.2f}"
            print(line)
        if any(info.get("estimated_cost_usd") is not None for info in preview.values()) and not yes:
            if not click.confirm("Continue with enrichment?", default=False):
                print("[enrich] Aborted.")
                return {"enriched": 0, "failed": 0, "pending": 0, "completed": 0, "aborted": True}

    init_llm()
    from enrichment.graph import _judge_provider, _judge_config
    _log(f"[enrich] Provider: {_judge_provider}")
    _log(f"[enrich] Credentials OK.{' (retry mode)' if retry else ''}")

    available = list_providers()
    targets = catalog_providers if catalog_providers else available
    targets = [p for p in targets if p in available]

    if not targets:
        print("[enrich] No catalog files found. Run sync first.")
        return {"enriched": 0, "failed": 0, "pending": 0, "completed": 0}

    enriched = 0
    failed = 0
    enriched_ids: set[str] = set()

    for cat_provider in targets:
        voices = load_catalog(cat_provider)
        if voices is None:
            continue

        pending = [(i, v) for i, v in enumerate(voices) if _needs_enrichment(v, retry=retry)]
        if limit is not None:
            pending = pending[:limit]
        if not pending:
            _log(f"[enrich] {cat_provider}: nothing to enrich")
            continue

        _log(f"[enrich] {cat_provider}: {len(pending)} voices to enrich")
        dirty = False

        for count, (idx, voice) in enumerate(pending, 1):
            vid = voice.get("id", "?")
            run_started_at = datetime.now(timezone.utc).isoformat()

            try:
                result = enrich_voice_graph(voice)
            except Exception as e:
                _log(f"[enrich] {vid}: graph error: {e}")
                voices[idx] = _set_status(voice, "failed", str(e)[:60])
                record_pipeline_run(
                    "enrich",
                    "failed",
                    provider=cat_provider,
                    voice_id=vid,
                    details={"error": str(e)[:60]},
                    started_at=run_started_at,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
                failed += 1
                dirty = True
                continue

            if result["status"] == "completed" and result.get("scores"):
                scores = result["scores"]
                scores["description"] = result.get("description")
                scores["enrichment"] = {
                    "provider": _judge_provider,
                    "model": (_judge_config or {}).get("model", ""),
                    "attempts": result.get("attempt", 1),
                    "sample_text": SAMPLE_TEXT,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                voices[idx] = merge_enrichment(voice, scores)
                record_pipeline_run(
                    "enrich",
                    "completed",
                    provider=cat_provider,
                    voice_id=vid,
                    details={"attempt": result.get("attempt", 1)},
                    started_at=run_started_at,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
                enriched += 1
                enriched_ids.add(vid)
            else:
                reason = "; ".join(result.get("validation_errors", []))[:80] or "graph_failed"
                voices[idx] = _set_status(voice, "failed", reason)
                record_pipeline_run(
                    "enrich",
                    "failed",
                    provider=cat_provider,
                    voice_id=vid,
                    details={"error": reason},
                    started_at=run_started_at,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
                failed += 1

            dirty = True

            # Cleanup temp audio
            audio_path = result.get("audio_path")
            if audio_path:
                try:
                    Path(audio_path).unlink(missing_ok=True)
                except Exception:
                    pass

            if count % 25 == 0:
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
        print("[enrich] Updating search index...")
        try:
            from audition.index import run_index
            run_index(changed_ids=enriched_ids)
        except Exception as e:
            _log(f"[enrich] Index update failed: {e}")

    return {"enriched": enriched, "failed": failed, "pending": pending_total, "completed": completed}
