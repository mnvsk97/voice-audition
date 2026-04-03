"""Common utilities for voice catalog sync scripts."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

CATALOG_DIR = Path(__file__).parent.parent / "catalog" / "voices"


def ensure_catalog_dir():
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)


def write_catalog(provider: str, voices: list[dict]):
    """Write normalized voice data for a provider."""
    ensure_catalog_dir()
    path = CATALOG_DIR / f"{provider}.json"
    data = {
        "provider": provider,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "voice_count": len(voices),
        "voices": voices,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[{provider}] Wrote {len(voices)} voices to {path}")


def make_voice_id(provider: str, provider_voice_id: str) -> str:
    return f"{provider}:{provider_voice_id}"


def normalize_voice(
    provider: str,
    provider_voice_id: str,
    name: str,
    *,
    provider_model: str | None = None,
    description: str | None = None,
    gender: str = "unknown",
    age_group: str = "unknown",
    accent: str | None = None,
    language: str = "en",
    additional_languages: list[str] | None = None,
    traits: dict | None = None,
    use_cases: list[str] | None = None,
    personality_tags: list[str] | None = None,
    style_tags: list[str] | None = None,
    preview_url: str | None = None,
    provider_page_url: str | None = None,
    popularity_score: float | None = None,
    metadata_source: str = "provider_api",
    provider_metadata: dict | None = None,
) -> dict:
    return {
        "id": make_voice_id(provider, provider_voice_id),
        "provider": provider,
        "provider_voice_id": provider_voice_id,
        "provider_model": provider_model,
        "name": name,
        "description": description,
        "gender": gender,
        "age_group": age_group,
        "accent": accent,
        "language": language,
        "additional_languages": additional_languages or [],
        "traits": traits or {"warmth": None, "energy": None, "clarity": None, "authority": None, "friendliness": None, "pace": None},
        "use_cases": use_cases or [],
        "personality_tags": personality_tags or [],
        "style_tags": style_tags or [],
        "preview_url": preview_url,
        "provider_page_url": provider_page_url,
        "popularity_score": popularity_score,
        "metadata_source": metadata_source,
        "provider_metadata": provider_metadata or {},
        "last_verified": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }
