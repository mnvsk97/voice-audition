"""
Sync Rime voices into catalog/rime.json.
No API key required — public JSON endpoint.
562+ voices across mist, mistv2, and arcana models.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

CATALOG_DIR = Path(__file__).parent.parent / "catalog"
OUTPUT = CATALOG_DIR / "rime.json"
URL = "https://users.rime.ai/data/voices/all-v2.json"


def fetch_voices() -> dict:
    req = Request(URL, headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def normalize_voice(name: str, model: str, language: str) -> dict:
    # Rime provides zero metadata beyond name — traits are unknown
    # Map language codes
    lang_map = {
        "eng": "en", "spa": "es", "fra": "fr", "ger": "de",
        "hin": "hi", "ara": "ar", "heb": "he", "jpn": "ja", "por": "pt",
    }
    lang = lang_map.get(language, language)

    # Map model to latency/cost
    model_info = {
        "mist": {"latency": "fastest", "cost": 0.008},
        "mistv2": {"latency": "fastest", "cost": 0.008},
        "arcana": {"latency": "fast", "cost": 0.012},
    }
    info = model_info.get(model, {"latency": "fast", "cost": 0.010})

    return {
        "id": f"rime:{model}:{name}",
        "provider": "rime",
        "provider_voice_id": name,
        "name": name.replace("_", " ").title(),
        "description": f"Rime {model} voice. {lang.upper()} language.",
        "gender": "unknown",
        "age": "unknown",
        "accent": "unknown",
        "language": lang,
        "languages": [lang],
        "traits": {
            "warmth": None,
            "energy": None,
            "clarity": None,
            "authority": None,
            "friendliness": None,
        },
        "use_cases": [],
        "personality": [],
        "tags": [model],
        "latency_tier": info["latency"],
        "cost_per_min_usd": info["cost"],
        "preview_url": None,
        "pipecat_supported": True,
        "pipecat_class": "RimeTTSService",
        "last_synced": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print("Syncing Rime voices...")
    data = fetch_voices()
    voices = []

    for model_name, languages in data.items():
        if not isinstance(languages, dict):
            continue
        for lang_code, voice_list in languages.items():
            if not isinstance(voice_list, list):
                continue
            for name in voice_list:
                voices.append(normalize_voice(name, model_name, lang_code))

    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(voices, indent=2, ensure_ascii=False))
    print(f"Done. {len(voices)} voices written to {OUTPUT}")


if __name__ == "__main__":
    main()
