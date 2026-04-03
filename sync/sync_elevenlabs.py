"""Sync voices from ElevenLabs shared voice library.

ElevenLabs has the richest metadata of any provider:
- gender, age, accent, language, descriptive tags, use_case
- preview_url (free audio preview)
- popularity signals (usage counts, cloned_by_count)

No auth required for the shared-voices endpoint.
"""

import os
import httpx
from common import normalize_voice, write_catalog

API_URL = "https://api.elevenlabs.io/v1/shared-voices"
PAGE_SIZE = 100
API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")


def map_age(age: str | None) -> str:
    if not age:
        return "unknown"
    age = age.lower()
    if age in ("young",):
        return "young"
    if age in ("middle_aged", "middle aged", "middle-aged"):
        return "middle"
    if age in ("old", "senior", "mature"):
        return "mature"
    return "unknown"


def map_gender(gender: str | None) -> str:
    if not gender:
        return "unknown"
    g = gender.lower()
    if g in ("male", "female", "neutral"):
        return g
    return "unknown"


def extract_popularity(voice: dict) -> float | None:
    usage_1y = voice.get("usage_character_count_1y", 0) or 0
    cloned = voice.get("cloned_by_count", 0) or 0
    if usage_1y == 0 and cloned == 0:
        return None
    # Rough normalization: top voices have ~100M usage chars
    score = min(1.0, (usage_1y / 100_000_000) * 0.7 + (cloned / 10_000) * 0.3)
    return round(score, 4)


def sync():
    voices = []
    cursor = None
    page = 0

    headers = {}
    if API_KEY:
        headers["xi-api-key"] = API_KEY
    else:
        print("[elevenlabs] WARNING: No ELEVENLABS_API_KEY set. API may require auth.")

    with httpx.Client(timeout=30, headers=headers) as client:
        while True:
            params = {"page_size": PAGE_SIZE}
            if cursor:
                params["last_sort_id"] = cursor

            resp = client.get(API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            batch = data.get("voices", [])
            if not batch:
                break

            for v in batch:
                voice_id = v.get("voice_id", "")
                if not voice_id:
                    continue

                name = v.get("name", "").strip()
                if not name:
                    continue

                accent = v.get("accent", "")
                descriptive = v.get("descriptive", "")
                use_case = v.get("use_case", "")
                category = v.get("category", "")

                style_tags = []
                if descriptive:
                    style_tags = [t.strip().lower() for t in descriptive.split(",") if t.strip()]

                use_cases = []
                if use_case:
                    use_cases = [u.strip().lower().replace(" ", "_") for u in use_case.split(",") if u.strip()]

                preview = v.get("preview_url")

                voices.append(normalize_voice(
                    provider="elevenlabs",
                    provider_voice_id=voice_id,
                    name=name,
                    provider_model="eleven_turbo_v2_5",
                    description=f"{name}. {descriptive}. {use_case}." if descriptive else name,
                    gender=map_gender(v.get("gender")),
                    age_group=map_age(v.get("age")),
                    accent=accent.lower() if accent else None,
                    language=v.get("language", "en"),
                    additional_languages=[lang.get("language", "") for lang in v.get("verified_languages", []) if lang.get("language")],
                    style_tags=style_tags,
                    use_cases=use_cases,
                    preview_url=preview,
                    provider_page_url="https://elevenlabs.io/voice-library",
                    popularity_score=extract_popularity(v),
                    metadata_source="provider_api",
                    provider_metadata={
                        "category": category,
                        "cloned_by_count": v.get("cloned_by_count"),
                        "usage_character_count_1y": v.get("usage_character_count_1y"),
                        "free_users_allowed": v.get("free_users_allowed"),
                        "featured": v.get("featured"),
                        "rate": v.get("rate"),
                    },
                ))

            cursor = data.get("last_sort_id")
            page += 1
            print(f"[elevenlabs] Page {page}: {len(batch)} voices (total: {len(voices)})")

            if not data.get("has_more", True) or not cursor:
                break

    write_catalog("elevenlabs", voices)


if __name__ == "__main__":
    sync()
