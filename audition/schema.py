from datetime import datetime, timezone

SCHEMA_VERSION = "1.1"

GENDERS = {"male", "female", "neutral", "unknown"}
AGE_GROUPS = {"young", "middle", "mature", "unknown"}
TEXTURES = {"smooth", "warm", "crisp", "gravelly", "breathy", "raspy", "rich", "thin"}
PITCHES = {"low", "medium-low", "medium", "medium-high", "high"}
TRAITS = {"warmth", "energy", "clarity", "authority", "friendliness", "confidence"}

USE_CASES = {
    "healthcare", "customer_support", "sales", "education", "finance",
    "meditation", "audiobook", "assistant", "voicemail", "entertainment",
    "advertisement", "podcast", "navigation", "gaming", "ivr", "storytelling",
}

PERSONALITY_TAGS = {
    "reassuring", "direct", "playful", "wise", "gentle", "confident",
    "warm", "calm", "energetic", "professional", "friendly", "authoritative",
    "sincere", "empathetic", "cheerful", "serious", "patient", "composed",
}

STYLE_TAGS = {
    "conversational", "formal", "animated", "soothing", "crisp", "measured",
    "expressive", "monotone", "casual", "dramatic", "deliberate", "upbeat",
    "relaxed", "articulate",
}

TRAIT_DEFAULTS = {t: None for t in TRAITS}


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
        "gender": gender if gender in GENDERS else "unknown",
        "age_group": age_group if age_group in AGE_GROUPS else "unknown",
        "accent": accent,
        "language": language,
        "additional_languages": additional_languages or [],
        "traits": {**TRAIT_DEFAULTS, **(traits or {})},
        "texture": texture if texture in TEXTURES else None,
        "pitch": pitch if pitch in PITCHES else None,
        "use_cases": [u for u in (use_cases or []) if u in USE_CASES],
        "personality_tags": [p for p in (personality_tags or []) if p in PERSONALITY_TAGS],
        "style_tags": [s for s in (style_tags or []) if s in STYLE_TAGS],
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
