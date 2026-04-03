"""
Voice catalog sync — consolidated provider sync functions.

Usage (as module):
    from voice_audition.sync import run_sync
    run_sync()                      # Sync all providers
    run_sync(["elevenlabs", "rime"])  # Sync specific providers

Usage (CLI):
    python -m voice_audition.sync.providers                   # Sync all
    python -m voice_audition.sync.providers elevenlabs rime   # Sync specific
    python -m voice_audition.sync.providers --list            # Show providers
"""

import json
import os
import sys
import traceback
from pathlib import Path

import httpx

from voice_audition.schema import make_voice

CATALOG_DIR = Path(__file__).parent.parent.parent.parent / "catalog"


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def write_catalog(provider: str, voices: list[dict]):
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    path = CATALOG_DIR / f"{provider}.json"
    path.write_text(json.dumps(voices, indent=2, ensure_ascii=False))
    print(f"[{provider}] Wrote {len(voices)} voices to {path}")


def map_gender(g: str | None) -> str:
    if not g:
        return "unknown"
    g = g.lower().strip()
    if g in ("male", "female", "neutral"):
        return g
    if g in ("masculine",):
        return "male"
    if g in ("feminine",):
        return "female"
    if g in ("gender_neutral",):
        return "neutral"
    return "unknown"


def map_age(a: str | None) -> str:
    if not a:
        return "unknown"
    a = a.lower().strip()
    if a in ("young", "young_adult", "youth"):
        return "young"
    if a in ("middle", "middle_aged", "middle aged", "middle-aged", "adult"):
        return "middle"
    if a in ("old", "senior", "mature"):
        return "mature"
    return "unknown"


# ---------------------------------------------------------------------------
# ElevenLabs — API sync (requires ELEVENLABS_API_KEY)
# ---------------------------------------------------------------------------

def sync_elevenlabs():
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("[elevenlabs] WARNING: No ELEVENLABS_API_KEY. Skipping.")
        return

    headers = {"xi-api-key": api_key}
    voices = []
    cursor = None
    page = 0

    with httpx.Client(timeout=30, headers=headers) as client:
        while True:
            params = {"page_size": 100}
            if cursor:
                params["last_sort_id"] = cursor

            resp = client.get("https://api.elevenlabs.io/v1/shared-voices", params=params)
            resp.raise_for_status()
            data = resp.json()

            batch = data.get("voices", [])
            if not batch:
                break

            for v in batch:
                vid = v.get("voice_id", "")
                name_ = v.get("name", "").strip()
                if not vid or not name_:
                    continue

                accent_ = v.get("accent", "")
                descriptive = v.get("descriptive", "")
                use_case = v.get("use_case", "")

                style_tags = [t.strip().lower() for t in descriptive.split(",") if t.strip()] if descriptive else []
                use_cases = [u.strip().lower().replace(" ", "_") for u in use_case.split(",") if u.strip()] if use_case else []

                usage_1y = v.get("usage_character_count_1y", 0) or 0
                cloned = v.get("cloned_by_count", 0) or 0

                voices.append(make_voice(
                    provider="elevenlabs",
                    provider_voice_id=vid,
                    name=name_,
                    provider_model="eleven_turbo_v2_5",
                    description=f"{name_}. {descriptive}. {use_case}." if descriptive else name_,
                    gender=map_gender(v.get("gender")),
                    age_group=map_age(v.get("age")),
                    accent=accent_.lower() if accent_ else None,
                    language=v.get("language", "en"),
                    additional_languages=[l.get("language", "") for l in v.get("verified_languages", []) if l.get("language")],
                    style_tags=style_tags,
                    use_cases=use_cases,
                    preview_url=v.get("preview_url"),
                    provider_page_url="https://elevenlabs.io/voice-library",
                    provider_metadata={
                        "category": v.get("category"),
                        "cloned_by_count": cloned,
                        "usage_character_count_1y": usage_1y,
                        "free_users_allowed": v.get("free_users_allowed"),
                        "featured": v.get("featured"),
                    },
                ))

            cursor = data.get("last_sort_id")
            page += 1
            print(f"[elevenlabs] Page {page}: {len(batch)} voices (total: {len(voices)})")

            if not data.get("has_more", True) or not cursor:
                break

    write_catalog("elevenlabs", voices)


# ---------------------------------------------------------------------------
# Rime — static JSON, no auth
# ---------------------------------------------------------------------------

RIME_LANG_MAP = {
    "eng": "en", "spa": "es", "fra": "fr", "ger": "de",
    "hin": "hi", "ara": "ar", "heb": "he", "jpn": "ja", "por": "pt",
}


def sync_rime():
    resp = httpx.get("https://users.rime.ai/data/voices/all-v2.json", timeout=30)
    resp.raise_for_status()
    data = resp.json()

    voices = []
    for model_family, languages in data.items():
        if not isinstance(languages, dict):
            continue
        for lang_code, names in languages.items():
            if not isinstance(names, list):
                continue
            iso = RIME_LANG_MAP.get(lang_code, lang_code)
            for n in names:
                if not isinstance(n, str) or not n.strip():
                    continue
                voices.append(make_voice(
                    provider="rime",
                    provider_voice_id=f"{model_family}:{n}",
                    name=n.replace("_", " ").title(),
                    provider_model=model_family,
                    language=iso,
                    provider_page_url="https://rime.ai",
                    provider_metadata={"model_family": model_family, "original_lang_code": lang_code},
                ))

    write_catalog("rime", voices)


# ---------------------------------------------------------------------------
# Deepgram — hardcoded registry (no listing API)
# ---------------------------------------------------------------------------

DEEPGRAM_VOICES = [
    ("Thalia", "aura-2-thalia-en", "female", "middle", "american"),
    ("Andromeda", "aura-2-andromeda-en", "female", "young", "american"),
    ("Arcas", "aura-2-arcas-en", "male", "young", "american"),
    ("Asteria", "aura-2-asteria-en", "female", "middle", "american"),
    ("Athena", "aura-2-athena-en", "female", "middle", "british"),
    ("Atlas", "aura-2-atlas-en", "male", "middle", "american"),
    ("Helios", "aura-2-helios-en", "male", "middle", "british"),
    ("Hera", "aura-2-hera-en", "female", "mature", "american"),
    ("Luna", "aura-2-luna-en", "female", "young", "american"),
    ("Orion", "aura-2-orion-en", "male", "middle", "american"),
    ("Perseus", "aura-2-perseus-en", "male", "young", "american"),
    ("Stella", "aura-2-stella-en", "female", "young", "american"),
    ("Zeus", "aura-2-zeus-en", "male", "mature", "american"),
    ("Angus", "aura-2-angus-en", "male", "middle", "irish"),
    ("Apollo", "aura-2-apollo-en", "male", "middle", "american"),
    ("Cora", "aura-2-cora-en", "female", "middle", "american"),
    ("Daphne", "aura-2-daphne-en", "female", "young", "british"),
    ("Echo", "aura-2-echo-en", "male", "young", "american"),
    ("Electra", "aura-2-electra-en", "female", "young", "american"),
    ("Harmony", "aura-2-harmony-en", "female", "middle", "australian"),
    ("Helena", "aura-2-helena-en", "female", "middle", "american"),
    ("Hercules", "aura-2-hercules-en", "male", "mature", "american"),
    ("Hermes", "aura-2-hermes-en", "male", "young", "american"),
    ("Iris", "aura-2-iris-en", "female", "young", "american"),
    ("Jason", "aura-2-jason-en", "male", "middle", "american"),
    ("Juno", "aura-2-juno-en", "female", "middle", "american"),
    ("Leda", "aura-2-leda-en", "female", "young", "american"),
    ("Lyra", "aura-2-lyra-en", "female", "young", "american"),
    ("Minerva", "aura-2-minerva-en", "female", "mature", "american"),
    ("Neptune", "aura-2-neptune-en", "male", "mature", "british"),
    ("Odysseus", "aura-2-odysseus-en", "male", "middle", "american"),
    ("Ophelia", "aura-2-ophelia-en", "female", "young", "american"),
    ("Orpheus", "aura-2-orpheus-en", "male", "young", "american"),
    ("Pandora", "aura-2-pandora-en", "female", "middle", "american"),
    ("Phoenix", "aura-2-phoenix-en", "male", "young", "american"),
    ("Poseidon", "aura-2-poseidon-en", "male", "mature", "american"),
    ("Selene", "aura-2-selene-en", "female", "middle", "american"),
    ("Titan", "aura-2-titan-en", "male", "middle", "american"),
    ("Triton", "aura-2-triton-en", "male", "young", "american"),
    ("Vesta", "aura-2-vesta-en", "female", "middle", "american"),
]


def sync_deepgram():
    voices = []
    for name_, vid, gender_, age_, accent_ in DEEPGRAM_VOICES:
        model = "aura-2" if vid.startswith("aura-2") else "aura-1"
        voices.append(make_voice(
            provider="deepgram", provider_voice_id=vid, name=name_,
            provider_model=model, gender=gender_, age_group=age_, accent=accent_,
            language="en", provider_page_url="https://deepgram.com/product/text-to-speech",
            metadata_source="manual",
        ))
    write_catalog("deepgram", voices)


# ---------------------------------------------------------------------------
# OpenAI — hardcoded (13 voices, no listing API)
# ---------------------------------------------------------------------------

OPENAI_VOICES = [
    ("Alloy", "alloy", "neutral", "middle", "american", "Neutral, versatile. Safe default for diverse audiences."),
    ("Ash", "ash", "male", "young", "american", "Soft-spoken, thoughtful. Calm and measured."),
    ("Ballad", "ballad", "male", "middle", "american", "Warm, melodic with gentle delivery."),
    ("Cedar", "cedar", "male", "middle", "american", "Grounded, steady. Reliable and clear."),
    ("Coral", "coral", "female", "young", "american", "Bright, warm. Friendly and engaging."),
    ("Echo", "echo", "male", "middle", "american", "Balanced. Reliable for long sessions."),
    ("Fable", "fable", "male", "middle", "british", "Expressive, storytelling with British accent."),
    ("Marin", "marin", "female", "young", "american", "Clear, youthful. Professional and articulate."),
    ("Nova", "nova", "female", "young", "american", "Bright and engaging. Great for consumer apps."),
    ("Onyx", "onyx", "male", "mature", "american", "Deep, commanding. Premium executive feel."),
    ("Sage", "sage", "female", "middle", "american", "Wise, calm. Measured and thoughtful."),
    ("Shimmer", "shimmer", "female", "middle", "american", "Warm, soothing. Care and wellness."),
    ("Verse", "verse", "male", "young", "american", "Dynamic, expressive. Good range and energy."),
]


def sync_openai():
    voices = []
    for name_, vid, gender_, age_, accent_, desc in OPENAI_VOICES:
        voices.append(make_voice(
            provider="openai", provider_voice_id=vid, name=name_,
            provider_model="gpt-4o-mini-tts", description=desc,
            gender=gender_, age_group=age_, accent=accent_, language="en",
            metadata_source="manual",
            provider_metadata={"supports_instructions": True},
        ))
    write_catalog("openai", voices)


# ---------------------------------------------------------------------------
# Cartesia — stub (requires API key)
# ---------------------------------------------------------------------------

def sync_cartesia():
    api_key = os.environ.get("CARTESIA_API_KEY", "")
    if not api_key:
        print("[cartesia] Requires CARTESIA_API_KEY. Skipping.")
        return


# ---------------------------------------------------------------------------
# PlayHT — stub (requires API key)
# ---------------------------------------------------------------------------

def sync_playht():
    api_key = os.environ.get("PLAYHT_API_KEY", "")
    if not api_key:
        print("[playht] Requires PLAYHT_API_KEY. Skipping.")
        return


# ---------------------------------------------------------------------------
# Registry & entry points
# ---------------------------------------------------------------------------

PROVIDERS = {
    "elevenlabs": sync_elevenlabs,
    "rime": sync_rime,
    "deepgram": sync_deepgram,
    "openai": sync_openai,
    "cartesia": sync_cartesia,
    "playht": sync_playht,
}


def run_sync(providers: list[str] | None = None):
    targets = providers or list(PROVIDERS.keys())

    results = {}
    for name in targets:
        fn = PROVIDERS.get(name)
        if not fn:
            print(f"Unknown provider: {name}")
            results[name] = "unknown"
            continue
        try:
            print(f"\n{'='*50}\nSyncing {name}\n{'='*50}")
            fn()
            results[name] = "ok"
        except Exception as e:
            print(f"[{name}] FAILED: {e}")
            traceback.print_exc()
            results[name] = f"failed: {e}"

    print(f"\n{'='*50}\nResults:")
    for name, status in results.items():
        print(f"  {name}: {status}")

    if any("failed" in str(v) for v in results.values()):
        sys.exit(1)


def main():
    args = sys.argv[1:]

    if "--list" in args:
        print("Available providers:", ", ".join(PROVIDERS.keys()))
        return

    targets = [a for a in args if not a.startswith("-")] or None
    run_sync(targets)


if __name__ == "__main__":
    main()
