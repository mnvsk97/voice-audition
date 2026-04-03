"""
Sync OpenAI TTS voices into catalog/openai.json.
No API needed — voices are hardcoded (OpenAI has no listing API).
13 voices total. Manually curated with trait data.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

CATALOG_DIR = Path(__file__).parent.parent / "catalog"
OUTPUT = CATALOG_DIR / "openai.json"

# Manually curated — OpenAI has no voice listing API
VOICES = [
    {
        "voice_id": "alloy", "name": "Alloy", "gender": "neutral", "age": "middle",
        "description": "Gender-neutral, versatile. Safe default for diverse audiences. Works across many use cases.",
        "traits": {"warmth": 0.6, "energy": 0.5, "clarity": 0.85, "authority": 0.5, "friendliness": 0.6},
        "use_cases": ["general", "tech_support", "education"],
        "personality": ["professional", "friendly", "trustworthy"],
    },
    {
        "voice_id": "ash", "name": "Ash", "gender": "male", "age": "young",
        "description": "Youthful male voice with a casual, approachable quality.",
        "traits": {"warmth": 0.65, "energy": 0.6, "clarity": 0.8, "authority": 0.35, "friendliness": 0.75},
        "use_cases": ["general", "education", "retail"],
        "personality": ["friendly", "casual", "approachable"],
    },
    {
        "voice_id": "ballad", "name": "Ballad", "gender": "male", "age": "middle",
        "description": "Warm, smooth male voice with a storytelling quality. Good for narration.",
        "traits": {"warmth": 0.75, "energy": 0.4, "clarity": 0.85, "authority": 0.55, "friendliness": 0.65},
        "use_cases": ["education", "general", "hospitality"],
        "personality": ["calm", "trustworthy", "warm"],
    },
    {
        "voice_id": "cedar", "name": "Cedar", "gender": "male", "age": "mature",
        "description": "Mature, grounded male voice. Steady and reliable.",
        "traits": {"warmth": 0.55, "energy": 0.4, "clarity": 0.9, "authority": 0.75, "friendliness": 0.45},
        "use_cases": ["finance", "legal", "general"],
        "personality": ["professional", "authoritative", "trustworthy"],
    },
    {
        "voice_id": "coral", "name": "Coral", "gender": "female", "age": "young",
        "description": "Bright, warm female voice. Friendly and engaging.",
        "traits": {"warmth": 0.8, "energy": 0.65, "clarity": 0.85, "authority": 0.3, "friendliness": 0.85},
        "use_cases": ["customer_support", "retail", "general"],
        "personality": ["friendly", "energetic", "warm"],
    },
    {
        "voice_id": "echo", "name": "Echo", "gender": "male", "age": "middle",
        "description": "Balanced male voice. Reliable and easy to listen to for long sessions.",
        "traits": {"warmth": 0.6, "energy": 0.5, "clarity": 0.85, "authority": 0.6, "friendliness": 0.55},
        "use_cases": ["education", "general", "tech_support"],
        "personality": ["professional", "trustworthy", "calm"],
    },
    {
        "voice_id": "marin", "name": "Marin", "gender": "female", "age": "middle",
        "description": "Clear, composed female voice. Professional with a touch of warmth.",
        "traits": {"warmth": 0.65, "energy": 0.45, "clarity": 0.9, "authority": 0.6, "friendliness": 0.6},
        "use_cases": ["healthcare", "customer_support", "general"],
        "personality": ["professional", "calm", "trustworthy"],
    },
    {
        "voice_id": "nova", "name": "Nova", "gender": "female", "age": "young",
        "description": "Bright and engaging female voice. Great for consumer apps.",
        "traits": {"warmth": 0.75, "energy": 0.65, "clarity": 0.85, "authority": 0.35, "friendliness": 0.8},
        "use_cases": ["retail", "customer_support", "general"],
        "personality": ["friendly", "energetic", "playful"],
    },
    {
        "voice_id": "onyx", "name": "Onyx", "gender": "male", "age": "mature",
        "description": "Deep, commanding male voice. Premium, executive-level feel.",
        "traits": {"warmth": 0.45, "energy": 0.4, "clarity": 0.9, "authority": 0.85, "friendliness": 0.35},
        "use_cases": ["finance", "legal", "sales"],
        "personality": ["authoritative", "professional", "luxurious"],
    },
    {
        "voice_id": "sage", "name": "Sage", "gender": "neutral", "age": "middle",
        "description": "Thoughtful, measured neutral voice. Good for informational delivery.",
        "traits": {"warmth": 0.55, "energy": 0.45, "clarity": 0.9, "authority": 0.6, "friendliness": 0.5},
        "use_cases": ["education", "tech_support", "general"],
        "personality": ["professional", "calm", "trustworthy"],
    },
    {
        "voice_id": "shimmer", "name": "Shimmer", "gender": "female", "age": "middle",
        "description": "Warm, soothing female voice. Well-suited for care and wellness.",
        "traits": {"warmth": 0.8, "energy": 0.45, "clarity": 0.8, "authority": 0.4, "friendliness": 0.75},
        "use_cases": ["healthcare", "mental_health", "hospitality"],
        "personality": ["empathetic", "calm", "trustworthy"],
    },
    {
        "voice_id": "verse", "name": "Verse", "gender": "male", "age": "young",
        "description": "Expressive young male voice with dynamic range.",
        "traits": {"warmth": 0.7, "energy": 0.7, "clarity": 0.8, "authority": 0.4, "friendliness": 0.7},
        "use_cases": ["education", "retail", "general"],
        "personality": ["energetic", "friendly", "expressive"],
    },
    {
        "voice_id": "fable", "name": "Fable", "gender": "male", "age": "middle",
        "description": "Gentle, narrative male voice. Warm storyteller quality.",
        "traits": {"warmth": 0.75, "energy": 0.35, "clarity": 0.8, "authority": 0.45, "friendliness": 0.7},
        "use_cases": ["education", "hospitality", "general"],
        "personality": ["calm", "warm", "trustworthy"],
    },
]


def normalize_voice(v: dict) -> dict:
    return {
        "id": f"openai:{v['voice_id']}",
        "provider": "openai",
        "provider_voice_id": v["voice_id"],
        "name": v["name"],
        "description": v["description"] + " Supports gpt-4o-mini-tts instructions parameter for dynamic voice tuning.",
        "gender": v["gender"],
        "age": v["age"],
        "accent": "american",
        "language": "en",
        "languages": ["en"],
        "traits": v["traits"],
        "use_cases": v["use_cases"],
        "personality": v["personality"],
        "tags": ["instruction-tunable"],
        "latency_tier": "fast",
        "cost_per_min_usd": 0.020,
        "preview_url": None,
        "pipecat_supported": True,
        "pipecat_class": "OpenAITTSService",
        "last_synced": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print("Syncing OpenAI TTS voices...")
    voices = [normalize_voice(v) for v in VOICES]
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(voices, indent=2, ensure_ascii=False))
    print(f"Done. {len(voices)} voices written to {OUTPUT}")


if __name__ == "__main__":
    main()
