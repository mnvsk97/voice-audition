from __future__ import annotations

import tempfile
from pathlib import Path

import httpx

from audition.db import list_providers, load_voices, record_pipeline_run, save_acoustic_features
from enrichment.pipeline import generate_sample


def _load_optional_libs():
    try:
        import librosa  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise ImportError("Install voice-audition[acoustic] to run acoustic enrichment.") from exc
    try:
        import parselmouth  # type: ignore
    except ImportError:
        parselmouth = None
    return librosa, np, parselmouth


def compute_acoustic_profile(audio_path: str | Path) -> dict[str, float | None]:
    librosa, np, parselmouth = _load_optional_libs()
    samples, sample_rate = librosa.load(str(audio_path), sr=None)
    f0, _, _ = librosa.pyin(
        samples,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
    )
    f0_values = f0[~np.isnan(f0)] if f0 is not None else np.array([])
    duration = max(len(samples) / float(sample_rate or 1), 1e-6)
    onset_env = librosa.onset.onset_strength(y=samples, sr=sample_rate)
    speech_rate = float(librosa.beat.tempo(onset_envelope=onset_env, sr=sample_rate)[0] / 60.0)
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=samples, sr=sample_rate)))

    hnr = None
    if parselmouth is not None:
        sound = parselmouth.Sound(samples, sample_rate)
        harmonicity = sound.to_harmonicity()
        hnr = float(harmonicity.values[harmonicity.values != -200].mean()) if harmonicity.values.size else None

    return {
        "f0_mean_hz": float(np.mean(f0_values)) if f0_values.size else None,
        "f0_std_hz": float(np.std(f0_values)) if f0_values.size else None,
        "speech_rate_syl_per_sec": speech_rate / max(duration, 1.0),
        "hnr_db": hnr,
        "spectral_centroid_hz": centroid,
    }


def enrich_acoustic(providers: list[str] | None = None) -> dict:
    targets = providers or list_providers()
    processed = 0
    failed = 0

    with httpx.Client(timeout=30) as client:
        for provider in targets:
            for voice in load_voices(provider=provider):
                run_started_at = record_pipeline_run("acoustic", "running", provider=provider, voice_id=voice["id"])
                with tempfile.TemporaryDirectory(prefix="voice_acoustic_") as tmp:
                    audio_path, error = generate_sample(voice, Path(tmp), client)
                    if not audio_path:
                        failed += 1
                        record_pipeline_run("acoustic", "failed", provider=provider, voice_id=voice["id"], details={"error": error})
                        continue
                    try:
                        features = compute_acoustic_profile(audio_path)
                        save_acoustic_features(voice["id"], features)
                        processed += 1
                        record_pipeline_run("acoustic", "completed", provider=provider, voice_id=voice["id"], details=features)
                    except Exception as exc:
                        failed += 1
                        record_pipeline_run("acoustic", "failed", provider=provider, voice_id=voice["id"], details={"error": str(exc)})

    return {"processed": processed, "failed": failed}
