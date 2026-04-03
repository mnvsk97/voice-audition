"""Sync voices from Rime.

Rime publishes a static JSON at users.rime.ai/data/voices/all-v2.json.
562 voices across 3 model families. Zero metadata — just names grouped by model/language.
Metadata must be enriched via LLM classification.
"""

import httpx
from common import normalize_voice, write_catalog

VOICES_URL = "https://users.rime.ai/data/voices/all-v2.json"

LANGUAGE_MAP = {
    "eng": "en",
    "spa": "es",
    "fra": "fr",
    "ger": "de",
    "hin": "hi",
    "ara": "ar",
    "heb": "he",
    "jpn": "ja",
    "por": "pt",
}


def sync():
    resp = httpx.get(VOICES_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    voices = []

    for model_family, languages in data.items():
        if not isinstance(languages, dict):
            continue

        for lang_code, voice_names in languages.items():
            if not isinstance(voice_names, list):
                continue

            iso_lang = LANGUAGE_MAP.get(lang_code, lang_code)

            for name in voice_names:
                if not isinstance(name, str) or not name.strip():
                    continue

                voice_id = f"{model_family}-{name}-{lang_code}"

                voices.append(normalize_voice(
                    provider="rime",
                    provider_voice_id=name,
                    name=name.replace("_", " ").title(),
                    provider_model=model_family,
                    description=None,  # needs LLM enrichment
                    gender="unknown",  # needs LLM enrichment
                    language=iso_lang,
                    provider_page_url="https://rime.ai",
                    metadata_source="provider_api",
                    provider_metadata={
                        "model_family": model_family,
                        "original_lang_code": lang_code,
                    },
                ))

    write_catalog("rime", voices)


if __name__ == "__main__":
    sync()
