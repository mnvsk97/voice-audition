"""
VoiceAudition API — audition TTS voices for your AI agent.
"""

from __future__ import annotations

from fastapi import FastAPI, Query
from .models import (
    Provider, Requirements, ScoredVoice, UseCase,
)
from .engine import suggest
from .catalog import VOICES

app = FastAPI(
    title="VoiceAudition API",
    description="Audition TTS voices for your AI agent",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"service": "voice-audition", "voices": len(VOICES)}


@app.post("/suggest", response_model=list[ScoredVoice])
def suggest_voices(req: Requirements, top_n: int = Query(5, ge=1, le=20)):
    return suggest(req, top_n=top_n)


@app.get("/voices")
def list_voices(
    provider: Provider | None = None,
    use_case: UseCase | None = None,
):
    filtered = VOICES
    if provider:
        filtered = [v for v in filtered if v.provider == provider]
    if use_case:
        filtered = [v for v in filtered if use_case in v.best_for]
    return filtered


@app.get("/providers")
def list_providers():
    return {
        "providers": [
            {
                "name": p.value,
                "voice_count": len([v for v in VOICES if v.provider == p]),
            }
            for p in Provider
        ]
    }
