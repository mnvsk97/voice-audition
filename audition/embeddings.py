from __future__ import annotations

import math
import tempfile
from pathlib import Path

import httpx

from audition.db import get_embedding_rows, list_providers, load_voices, record_pipeline_run, save_embedding
from enrichment.pipeline import generate_sample


def _load_clap_model():
    try:
        import librosa  # type: ignore
        import torch  # type: ignore
        from transformers import AutoModel, AutoProcessor  # type: ignore
    except ImportError as exc:
        raise ImportError("Install voice-audition[clap] to run embeddings and audio search.") from exc

    model_id = "laion/clap-htsat-unfused"
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModel.from_pretrained(model_id)
    model.eval()
    return librosa, torch, processor, model


def embed_audio_file(audio_path: str | Path) -> list[float]:
    librosa, torch, processor, model = _load_clap_model()
    audio, sample_rate = librosa.load(str(audio_path), sr=48_000)
    inputs = processor(audios=audio, sampling_rate=sample_rate, return_tensors="pt")
    with torch.no_grad():
        features = model.get_audio_features(**inputs)
    return features[0].tolist()


def embed_voices(providers: list[str] | None = None) -> dict:
    targets = providers or list_providers()
    processed = 0
    failed = 0

    with httpx.Client(timeout=30) as client:
        for provider in targets:
            for voice in load_voices(provider=provider):
                with tempfile.TemporaryDirectory(prefix="voice_embed_") as tmp:
                    audio_path, error = generate_sample(voice, Path(tmp), client)
                    if not audio_path:
                        failed += 1
                        record_pipeline_run("embed", "failed", provider=provider, voice_id=voice["id"], details={"error": error})
                        continue
                    try:
                        vector = embed_audio_file(audio_path)
                        save_embedding(voice["id"], "clap", vector)
                        processed += 1
                        record_pipeline_run("embed", "completed", provider=provider, voice_id=voice["id"], details={"dimension": len(vector)})
                    except Exception as exc:
                        failed += 1
                        record_pipeline_run("embed", "failed", provider=provider, voice_id=voice["id"], details={"error": str(exc)})
    return {"processed": processed, "failed": failed}


def search_audio(audio_path: str | Path, top_k: int = 5) -> list[dict]:
    query = embed_audio_file(audio_path)
    query_norm = math.sqrt(sum(v * v for v in query)) or 1.0
    voice_index = {voice["id"]: voice for voice in load_voices()}

    scored = []
    for voice_id, vector in get_embedding_rows():
        denom = (math.sqrt(sum(v * v for v in vector)) or 1.0) * query_norm
        score = sum(a * b for a, b in zip(query, vector)) / denom
        voice = voice_index.get(voice_id)
        if voice:
            scored.append({**voice, "score": round(score, 4)})
    scored.sort(key=lambda row: -row["score"])
    return scored[:top_k]
