"""Voice schema — dict factory and validation. No classes, no pydantic."""

from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"

TRAIT_DEFAULTS = {
    "warmth": None,
    "energy": None,
    "clarity": None,
    "authority": None,
    "friendliness": None,
    "confidence": None,
    "expressiveness": None,
    "pace": None,
}

REQUIRED_FIELDS = ("id", "provider", "provider_voice_id", "name")

VALID_GENDERS = ("male", "female", "neutral", "unknown")
VALID_AGE_GROUPS = ("young", "middle", "mature", "unknown")
VALID_TEXTURES = (
    "smooth", "warm", "crisp", "gravelly", "breathy", "raspy", "rich", "thin", None,
)
VALID_PITCHES = ("low", "medium-low", "medium", "medium-high", "high", None)
VALID_SPEAKING_STYLES = (
    "conversational", "narration", "newscast", "customer_service",
    "meditation", "advertisement", "formal", "casual", None,
)
VALID_EMOTIONAL_RANGES = ("static", "basic", "expressive", "full", None)
VALID_STATUSES = ("active", "deprecated", "preview")
VALID_METADATA_SOURCES = (
    "provider_api", "enriched_local", "enriched_cloud", "manual", "hybrid",
)


def make_voice(
    provider: str,
    provider_voice_id: str,
    name: str,
    *,
    # identity
    provider_model: str | None = None,
    description: str | None = None,
    gender: str = "unknown",
    age_group: str = "unknown",
    accent: str | None = None,
    language: str = "en",
    additional_languages: list[str] | None = None,
    # traits (0-1 floats, nullable)
    traits: dict | None = None,
    # voice quality
    texture: str | None = None,
    pitch: str | None = None,
    speaking_style: str | None = None,
    # tags
    use_cases: list[str] | None = None,
    personality_tags: list[str] | None = None,
    style_tags: list[str] | None = None,
    # emotion
    emotional_range: str | None = None,
    supported_emotions: list[str] | None = None,
    # provider / tech
    latency_tier: str | None = None,
    cost_per_min_usd: float | None = None,
    preview_url: str | None = None,
    provider_page_url: str | None = None,
    pipecat_supported: bool = False,
    pipecat_class: str | None = None,
    status: str = "active",
    # enrichment
    metadata_source: str = "provider_api",
    enrichment: dict | None = None,
    # sync
    last_synced: str | None = None,
    last_verified: str | None = None,
    provider_metadata: dict | None = None,
) -> dict:
    """Build a voice dict matching the locked schema. Drop-in replacement for sync.voice()."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": SCHEMA_VERSION,
        # required
        "id": f"{provider}:{provider_voice_id}",
        "provider": provider,
        "provider_voice_id": provider_voice_id,
        "name": name,
        # identity
        "provider_model": provider_model,
        "description": description,
        "gender": gender,
        "age_group": age_group,
        "accent": accent,
        "language": language,
        "additional_languages": additional_languages or [],
        # traits
        "traits": {**TRAIT_DEFAULTS, **(traits or {})},
        # voice quality
        "texture": texture,
        "pitch": pitch,
        "speaking_style": speaking_style,
        # tags
        "use_cases": use_cases or [],
        "personality_tags": personality_tags or [],
        "style_tags": style_tags or [],
        # emotion
        "emotional_range": emotional_range,
        "supported_emotions": supported_emotions or [],
        # provider / tech
        "latency_tier": latency_tier,
        "cost_per_min_usd": cost_per_min_usd,
        "preview_url": preview_url,
        "provider_page_url": provider_page_url,
        "pipecat_supported": pipecat_supported,
        "pipecat_class": pipecat_class,
        "status": status,
        # enrichment
        "metadata_source": metadata_source,
        "enrichment": enrichment or {},
        # sync
        "last_synced": last_synced or now,
        "last_verified": last_verified or now,
        "provider_metadata": provider_metadata or {},
    }


def validate_voice(voice_dict: dict) -> list[str]:
    """Check required fields and value constraints. Returns list of errors (empty = valid)."""
    errors = []

    for field in REQUIRED_FIELDS:
        if not voice_dict.get(field):
            errors.append(f"missing required field: {field}")

    gender = voice_dict.get("gender")
    if gender and gender not in VALID_GENDERS:
        errors.append(f"invalid gender: {gender!r} (expected one of {VALID_GENDERS})")

    age_group = voice_dict.get("age_group")
    if age_group and age_group not in VALID_AGE_GROUPS:
        errors.append(f"invalid age_group: {age_group!r} (expected one of {VALID_AGE_GROUPS})")

    texture = voice_dict.get("texture")
    if texture is not None and texture not in VALID_TEXTURES:
        errors.append(f"invalid texture: {texture!r}")

    pitch = voice_dict.get("pitch")
    if pitch is not None and pitch not in VALID_PITCHES:
        errors.append(f"invalid pitch: {pitch!r}")

    speaking_style = voice_dict.get("speaking_style")
    if speaking_style is not None and speaking_style not in VALID_SPEAKING_STYLES:
        errors.append(f"invalid speaking_style: {speaking_style!r}")

    emotional_range = voice_dict.get("emotional_range")
    if emotional_range is not None and emotional_range not in VALID_EMOTIONAL_RANGES:
        errors.append(f"invalid emotional_range: {emotional_range!r}")

    status = voice_dict.get("status")
    if status and status not in VALID_STATUSES:
        errors.append(f"invalid status: {status!r}")

    metadata_source = voice_dict.get("metadata_source")
    if metadata_source and metadata_source not in VALID_METADATA_SOURCES:
        errors.append(f"invalid metadata_source: {metadata_source!r}")

    # Validate trait values are None or 0-1 floats
    traits = voice_dict.get("traits", {})
    if isinstance(traits, dict):
        for key, val in traits.items():
            if val is not None:
                if not isinstance(val, (int, float)) or not (0 <= val <= 1):
                    errors.append(f"trait {key!r} must be None or a float in [0, 1], got {val!r}")

    return errors
