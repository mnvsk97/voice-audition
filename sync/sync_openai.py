"""Sync voices from OpenAI TTS.

OpenAI has no voice listing API. 13 voices hardcoded in the SDK.
The gpt-4o-mini-tts model supports an `instructions` parameter for dynamic tuning.
"""

from common import normalize_voice, write_catalog

OPENAI_VOICES = [
    {"name": "Alloy", "id": "alloy", "gender": "neutral", "age": "middle", "desc": "Neutral, versatile. Safe default for diverse audiences. Balanced warmth and clarity."},
    {"name": "Ash", "id": "ash", "gender": "male", "age": "young", "desc": "Soft-spoken, thoughtful male voice. Calm and measured."},
    {"name": "Ballad", "id": "ballad", "gender": "male", "age": "middle", "desc": "Warm, melodic male voice with gentle delivery."},
    {"name": "Cedar", "id": "cedar", "gender": "male", "age": "middle", "desc": "Grounded, steady male voice. Reliable and clear."},
    {"name": "Coral", "id": "coral", "gender": "female", "age": "young", "desc": "Bright, warm female voice. Friendly and engaging."},
    {"name": "Echo", "id": "echo", "gender": "male", "age": "middle", "desc": "Balanced male voice. Reliable and easy to listen to for long sessions."},
    {"name": "Fable", "id": "fable", "gender": "male", "age": "middle", "desc": "Expressive, storytelling male voice with British accent."},
    {"name": "Marin", "id": "marin", "gender": "female", "age": "young", "desc": "Clear, youthful female voice. Professional and articulate."},
    {"name": "Nova", "id": "nova", "gender": "female", "age": "young", "desc": "Bright and engaging female voice. Great for consumer apps. Energetic."},
    {"name": "Onyx", "id": "onyx", "gender": "male", "age": "mature", "desc": "Deep, commanding male voice. Premium, executive-level feel."},
    {"name": "Sage", "id": "sage", "gender": "female", "age": "middle", "desc": "Wise, calm female voice. Measured and thoughtful delivery."},
    {"name": "Shimmer", "id": "shimmer", "gender": "female", "age": "middle", "desc": "Warm, soothing female voice. Well-suited for care and wellness."},
    {"name": "Verse", "id": "verse", "gender": "male", "age": "young", "desc": "Dynamic, expressive male voice. Good range and energy."},
]


def sync():
    voices = []

    for v in OPENAI_VOICES:
        voices.append(normalize_voice(
            provider="openai",
            provider_voice_id=v["id"],
            name=v["name"],
            provider_model="gpt-4o-mini-tts",
            description=v["desc"],
            gender=v["gender"],
            age_group=v["age"],
            accent="american" if v["id"] != "fable" else "british",
            language="en",
            metadata_source="manual",
            provider_metadata={
                "supports_instructions": True,
                "note": "Use instructions parameter on gpt-4o-mini-tts for dynamic voice tuning",
            },
        ))

    write_catalog("openai", voices)


if __name__ == "__main__":
    sync()
