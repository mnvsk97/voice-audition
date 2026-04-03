"""
Sync ElevenLabs voices into catalog/elevenlabs.json.

Two modes:
1. Without API key: pulls 21 premade voices from /v1/voices (no auth)
2. With ELEVENLABS_API_KEY: pulls 11,000+ shared voices from /v1/shared-voices
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

CATALOG_DIR = Path(__file__).parent.parent / "catalog"
OUTPUT = CATALOG_DIR / "elevenlabs.json"
PAGE_SIZE = 100
MAX_PAGES = 200


def fetch_json(url: str, headers: dict | None = None) -> dict:
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    req = Request(url, headers=hdrs)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def normalize_voice(v: dict, from_shared: bool = False) -> dict:
    labels = v.get("labels", {}) or {}
    name_raw = v.get("name", "")
    # Premade voices have "Name - Description" format
    name = name_raw.split(" - ")[0].strip() if " - " in name_raw else name_raw

    gender = labels.get("gender", v.get("gender", "unknown")) or "unknown"
    age_raw = labels.get("age", "unknown") or "unknown"
    accent = labels.get("accent", "unknown") or "unknown"
    use_case = labels.get("use_case", "") or ""
    descriptive = labels.get("descriptive", "") or ""
    language = labels.get("language", "en") or "en"

    if from_shared:
        gender = v.get("gender", gender) or gender
        accent = v.get("accent", accent) or accent
        age_raw = v.get("age", age_raw) or age_raw
        descriptive = v.get("descriptive", descriptive) or descriptive
        use_case = v.get("use_case", use_case) or use_case
        language = v.get("language", language) or language

    age_map = {"young": "young", "middle_aged": "middle", "middle aged": "middle", "old": "mature"}
    age = age_map.get(age_raw.lower().replace("-", "_").replace(" ", "_"), "unknown")

    tags = []
    if descriptive:
        tags.extend([t.strip().lower() for t in descriptive.split(",") if t.strip()])
    if use_case:
        tags.extend([t.strip().lower() for t in use_case.split(",") if t.strip()])

    # Description from name suffix or descriptive label
    desc_parts = []
    if " - " in name_raw:
        desc_parts.append(name_raw.split(" - ", 1)[1].strip())
    if descriptive and descriptive.lower() not in (name_raw.lower(),):
        desc_parts.append(descriptive)
    description = ". ".join(desc_parts) if desc_parts else ""

    voice_id = v.get("voice_id", v.get("public_owner_id", ""))

    return {
        "id": f"elevenlabs:{voice_id}",
        "provider": "elevenlabs",
        "provider_voice_id": voice_id,
        "name": name,
        "description": description,
        "gender": gender.lower(),
        "age": age,
        "accent": accent.lower(),
        "language": language.lower()[:2],
        "languages": list(set([language.lower()[:2]] if language else ["en"])),
        "traits": {"warmth": None, "energy": None, "clarity": None, "authority": None, "friendliness": None},
        "use_cases": [u.strip().lower() for u in use_case.split(",") if u.strip()] if use_case else [],
        "personality": [],
        "tags": tags,
        "latency_tier": "fast",
        "cost_per_min_usd": 0.030,
        "preview_url": v.get("preview_url"),
        "pipecat_supported": True,
        "pipecat_class": "ElevenLabsTTSService",
        "last_synced": datetime.now(timezone.utc).isoformat(),
    }


def sync_premade() -> list[dict]:
    """Fetch 21 premade voices — no auth needed."""
    print("  Fetching premade voices (no auth)...")
    data = fetch_json("https://api.elevenlabs.io/v1/voices")
    voices = data.get("voices", [])
    print(f"  Got {len(voices)} premade voices")
    return [normalize_voice(v, from_shared=False) for v in voices]


def sync_shared(api_key: str) -> list[dict]:
    """Fetch shared voice library — requires auth. 11,000+ voices."""
    print("  Fetching shared voices (with API key)...")
    voices = []
    cursor = None
    page = 0

    while page < MAX_PAGES:
        url = f"https://api.elevenlabs.io/v1/shared-voices?page_size={PAGE_SIZE}"
        if cursor:
            url += f"&last_sort_id={cursor}"
        try:
            data = fetch_json(url, headers={"xi-api-key": api_key})
        except HTTPError as e:
            print(f"  HTTP error on page {page}: {e.code}")
            break

        batch = data.get("voices", [])
        if not batch:
            break

        for v in batch:
            voices.append(normalize_voice(v, from_shared=True))

        cursor = data.get("last_sort_id")
        page += 1

        if page % 10 == 0:
            print(f"  Page {page}: {len(voices)} voices so far...")

        if not data.get("has_more", False):
            break
        time.sleep(0.2)

    print(f"  Got {len(voices)} shared voices")
    return voices


def main():
    print("Syncing ElevenLabs voices...")
    api_key = os.environ.get("ELEVENLABS_API_KEY")

    if api_key:
        voices = sync_shared(api_key)
        # Also add premade voices that might not be in shared
        premade = sync_premade()
        premade_ids = {v["provider_voice_id"] for v in premade}
        shared_ids = {v["provider_voice_id"] for v in voices}
        for v in premade:
            if v["provider_voice_id"] not in shared_ids:
                voices.append(v)
    else:
        print("  No ELEVENLABS_API_KEY set — using premade voices only (21 voices)")
        print("  Set ELEVENLABS_API_KEY to sync 11,000+ shared voices")
        voices = sync_premade()

    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(voices, indent=2, ensure_ascii=False))
    print(f"Done. {len(voices)} voices written to {OUTPUT}")


if __name__ == "__main__":
    main()
