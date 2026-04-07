"""Voice quality scoring — predicts MOS (1-5) from audio using UTMOS22."""
from __future__ import annotations

import tempfile
from pathlib import Path

import httpx

from audition.db import (
    get_acoustic_features,
    list_providers,
    load_voices,
    record_pipeline_run,
    save_utmos_score,
)


_cached_model = None


def _get_model():
    global _cached_model
    if _cached_model is None:
        try:
            import torch  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "Install voice-audition[utmos] (torch>=2.0) to run quality scoring."
            ) from exc
        model = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22", trust_repo=True)
        model.eval()
        _cached_model = (model, torch)
    return _cached_model


def predict_mos(audio_path: str) -> dict:
    """Predict MOS from audio using UTMOS22. Returns {"mos": float} (1-5 scale)."""
    import torchaudio  # type: ignore

    model, torch = _get_model()
    waveform, sr = torchaudio.load(audio_path)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if sr != 16000:
        waveform = torchaudio.functional.resample(waveform, sr, 16000)

    with torch.no_grad():
        score = model(waveform, sr=16000)

    return {"mos": round(max(1.0, min(5.0, float(score.mean()))), 3)}


def safe_predict_mos(audio_path: str | None) -> float | None:
    """Run quality prediction, returning None on any failure."""
    if not audio_path:
        return None
    try:
        return predict_mos(audio_path)["mos"]
    except Exception:
        return None


def score_voices(providers: list[str] | None = None) -> dict:
    """Batch-score voices with preview audio using UTMOS22."""
    from enrichment.pipeline import generate_sample

    targets = providers or list_providers()
    processed = 0
    failed = 0
    skipped = 0

    with httpx.Client(timeout=30) as client:
        for provider in targets:
            for voice in load_voices(provider=provider):
                existing = get_acoustic_features(voice["id"])
                if existing and existing.get("utmos_score") is not None:
                    skipped += 1
                    continue

                record_pipeline_run("quality", "running", provider=provider, voice_id=voice["id"])
                with tempfile.TemporaryDirectory(prefix="voice_mos_") as tmp:
                    audio_path, error = generate_sample(voice, Path(tmp), client)
                    if not audio_path:
                        failed += 1
                        record_pipeline_run("quality", "failed", provider=provider,
                                            voice_id=voice["id"], details={"error": error})
                        continue
                    try:
                        result = predict_mos(str(audio_path))
                        save_utmos_score(voice["id"], result["mos"])
                        processed += 1
                        record_pipeline_run("quality", "completed", provider=provider,
                                            voice_id=voice["id"], details=result)
                        print(f"  [quality] {voice.get('name', '?')} ({provider}): MOS={result['mos']:.2f}")
                    except Exception as exc:
                        failed += 1
                        record_pipeline_run("quality", "failed", provider=provider,
                                            voice_id=voice["id"], details={"error": str(exc)[:200]})

    return {"processed": processed, "failed": failed, "skipped": skipped}
