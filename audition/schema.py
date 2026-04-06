from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"

TRAIT_DEFAULTS = {
    "warmth": None, "energy": None, "clarity": None,
    "authority": None, "friendliness": None, "confidence": None,
}


def make_voice(
    provider: str, provider_voice_id: str, name: str, *,
    provider_model: str | None = None, description: str | None = None,
    gender: str = "unknown", age_group: str = "unknown",
    accent: str | None = None, language: str = "en",
    additional_languages: list[str] | None = None,
    traits: dict | None = None,
    texture: str | None = None, pitch: str | None = None,
    use_cases: list[str] | None = None,
    personality_tags: list[str] | None = None, style_tags: list[str] | None = None,
    latency_tier: str | None = None, cost_per_min_usd: float | None = None,
    preview_url: str | None = None, provider_page_url: str | None = None,
    pipecat_supported: bool = False, pipecat_class: str | None = None,
    status: str = "active",
    metadata_source: str = "provider_api", enrichment: dict | None = None,
    last_synced: str | None = None, last_verified: str | None = None,
    provider_metadata: dict | None = None,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": SCHEMA_VERSION,
        "id": f"{provider}:{provider_voice_id}",
        "provider": provider,
        "provider_voice_id": provider_voice_id,
        "name": name,
        "provider_model": provider_model,
        "description": description,
        "gender": gender,
        "age_group": age_group,
        "accent": accent,
        "language": language,
        "additional_languages": additional_languages or [],
        "traits": {**TRAIT_DEFAULTS, **(traits or {})},
        "texture": texture,
        "pitch": pitch,
        "use_cases": use_cases or [],
        "personality_tags": personality_tags or [],
        "style_tags": style_tags or [],
        "latency_tier": latency_tier,
        "cost_per_min_usd": cost_per_min_usd,
        "preview_url": preview_url,
        "provider_page_url": provider_page_url,
        "pipecat_supported": pipecat_supported,
        "pipecat_class": pipecat_class,
        "status": status,
        "metadata_source": metadata_source,
        "enrichment": enrichment or {},
        "last_synced": last_synced or now,
        "last_verified": last_verified or now,
        "provider_metadata": provider_metadata or {},
    }
