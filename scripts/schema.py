"""
Unified voice schema. Every provider normalizes into this format.
One JSON file per provider in catalog/<provider>.json, containing a list of these objects.
"""

VOICE_SCHEMA = {
    "id": "str — provider:voice_id (e.g. elevenlabs:21m00Tcm4TlvDq8ikWAM)",
    "provider": "str — elevenlabs|cartesia|deepgram|openai|playht|rime|azure|google|polly",
    "provider_voice_id": "str — the ID you pass to the provider API",
    "name": "str — human-readable name",
    "description": "str — what this voice sounds like, personality, best uses",
    "gender": "str — male|female|neutral|unknown",
    "age": "str — young|middle|mature|unknown",
    "accent": "str — american|british|australian|etc or unknown",
    "language": "str — primary language code e.g. en",
    "languages": "list[str] — all supported language codes",
    "traits": {
        "warmth": "float 0-1",
        "energy": "float 0-1",
        "clarity": "float 0-1",
        "authority": "float 0-1",
        "friendliness": "float 0-1",
    },
    "use_cases": "list[str] — healthcare, sales, support, education, etc",
    "personality": "list[str] — empathetic, professional, friendly, etc",
    "tags": "list[str] — free-form descriptive tags from provider",
    "latency_tier": "str — fastest|fast|standard",
    "cost_per_min_usd": "float — approximate cost in USD per minute",
    "preview_url": "str|null — URL to hear this voice (provider playground or audio file)",
    "pipecat_supported": "bool — whether Pipecat has a native service class for this provider",
    "pipecat_class": "str|null — e.g. CartesiaTTSService",
    "last_synced": "str — ISO timestamp of last sync",
}
