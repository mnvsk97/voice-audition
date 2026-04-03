"""
Sync Deepgram Aura voices into catalog/deepgram.json.
No listing API — voices are documented statically.
Maintained manually from https://developers.deepgram.com/docs/tts-models
"""

import json
from datetime import datetime, timezone
from pathlib import Path

CATALOG_DIR = Path(__file__).parent.parent / "catalog"
OUTPUT = CATALOG_DIR / "deepgram.json"

# Curated from Deepgram docs — Aura-2 English voices
VOICES = [
    {"voice_id": "aura-2-thalia-en", "name": "Thalia", "gender": "female", "age": "middle", "accent": "american", "desc": "Warm, professional female voice. Versatile for many use cases."},
    {"voice_id": "aura-2-andromeda-en", "name": "Andromeda", "gender": "female", "age": "young", "accent": "american", "desc": "Bright, energetic young female voice."},
    {"voice_id": "aura-2-asteria-en", "name": "Asteria", "gender": "female", "age": "middle", "accent": "american", "desc": "Balanced female voice. Best value for high-volume deployments."},
    {"voice_id": "aura-2-athena-en", "name": "Athena", "gender": "female", "age": "middle", "accent": "american", "desc": "Clear, authoritative female voice."},
    {"voice_id": "aura-2-helena-en", "name": "Helena", "gender": "female", "age": "middle", "accent": "american", "desc": "Warm, friendly female voice with a conversational quality."},
    {"voice_id": "aura-2-hera-en", "name": "Hera", "gender": "female", "age": "mature", "accent": "american", "desc": "Mature, commanding female voice."},
    {"voice_id": "aura-2-luna-en", "name": "Luna", "gender": "female", "age": "young", "accent": "american", "desc": "Bright, friendly female voice. Good for consumer-facing at scale."},
    {"voice_id": "aura-2-persephone-en", "name": "Persephone", "gender": "female", "age": "young", "accent": "american", "desc": "Soft, gentle young female voice."},
    {"voice_id": "aura-2-stella-en", "name": "Stella", "gender": "female", "age": "middle", "accent": "american", "desc": "Professional, polished female voice."},
    {"voice_id": "aura-2-apollo-en", "name": "Apollo", "gender": "male", "age": "middle", "accent": "american", "desc": "Strong, confident male voice."},
    {"voice_id": "aura-2-arcas-en", "name": "Arcas", "gender": "male", "age": "young", "accent": "american", "desc": "Youthful male voice. Approachable and easy to listen to."},
    {"voice_id": "aura-2-aries-en", "name": "Aries", "gender": "male", "age": "young", "accent": "american", "desc": "Energetic young male voice."},
    {"voice_id": "aura-2-helios-en", "name": "Helios", "gender": "male", "age": "middle", "accent": "american", "desc": "Warm, steady male voice."},
    {"voice_id": "aura-2-hermes-en", "name": "Hermes", "gender": "male", "age": "young", "accent": "american", "desc": "Quick, articulate young male voice."},
    {"voice_id": "aura-2-orpheus-en", "name": "Orpheus", "gender": "male", "age": "middle", "accent": "american", "desc": "Smooth, melodic male voice."},
    {"voice_id": "aura-2-orion-en", "name": "Orion", "gender": "male", "age": "middle", "accent": "american", "desc": "Clear male voice. Reliable workhorse for support and info delivery."},
    {"voice_id": "aura-2-perseus-en", "name": "Perseus", "gender": "male", "age": "middle", "accent": "american", "desc": "Confident, professional male voice."},
    {"voice_id": "aura-2-titan-en", "name": "Titan", "gender": "male", "age": "mature", "accent": "american", "desc": "Deep, authoritative mature male voice."},
    {"voice_id": "aura-2-zeus-en", "name": "Zeus", "gender": "male", "age": "mature", "accent": "american", "desc": "Commanding, powerful male voice."},
    # British accents
    {"voice_id": "aura-2-angus-en", "name": "Angus", "gender": "male", "age": "middle", "accent": "british", "desc": "British male voice. Professional and refined."},
    {"voice_id": "aura-2-cordelia-en", "name": "Cordelia", "gender": "female", "age": "middle", "accent": "british", "desc": "British female voice. Polished and warm."},
]


def normalize_voice(v: dict) -> dict:
    return {
        "id": f"deepgram:{v['voice_id']}",
        "provider": "deepgram",
        "provider_voice_id": v["voice_id"],
        "name": v["name"],
        "description": v["desc"],
        "gender": v["gender"],
        "age": v["age"],
        "accent": v["accent"],
        "language": "en",
        "languages": ["en"],
        "traits": {
            "warmth": None,
            "energy": None,
            "clarity": None,
            "authority": None,
            "friendliness": None,
        },
        "use_cases": [],
        "personality": [],
        "tags": ["aura-2"],
        "latency_tier": "fastest",
        "cost_per_min_usd": 0.010,
        "preview_url": None,
        "pipecat_supported": True,
        "pipecat_class": "DeepgramTTSService",
        "last_synced": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print("Syncing Deepgram Aura voices...")
    voices = [normalize_voice(v) for v in VOICES]
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(voices, indent=2, ensure_ascii=False))
    print(f"Done. {len(voices)} voices written to {OUTPUT}")


if __name__ == "__main__":
    main()
