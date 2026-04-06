import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import httpx

from audition.schema import make_voice
from enrichment import CATALOG_DIR


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_catalog(provider: str, voices: list[dict]):
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    (CATALOG_DIR / f"{provider}.json").write_text(json.dumps(voices, indent=2, ensure_ascii=False))


def load_existing(provider: str) -> list[dict]:
    path = CATALOG_DIR / f"{provider}.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def map_gender(g: str | None) -> str:
    if not g:
        return "unknown"
    g = g.lower().strip()
    if g in ("male", "female", "neutral"):
        return g
    return {"masculine": "male", "feminine": "female", "gender_neutral": "neutral"}.get(g, "unknown")


def map_age(a: str | None) -> str:
    if not a:
        return "unknown"
    a = a.lower().strip()
    for bucket, aliases in [("young", ("young", "young_adult", "youth")),
                            ("middle", ("middle", "middle_aged", "middle aged", "middle-aged", "adult")),
                            ("mature", ("old", "senior", "mature"))]:
        if a in aliases:
            return bucket
    return "unknown"


_ENRICHMENT_KEYS = (
    "description", "gender", "age_group", "accent", "traits", "texture", "pitch",
    "personality_tags", "style_tags", "use_cases", "enrichment", "metadata_source",
)
_ENRICHED_SOURCES = ("enriched_local", "enriched_cloud", "manual", "hybrid")
_PROVIDER_FIELDS = ("name", "provider_model", "preview_url", "provider_page_url", "provider_metadata")


def diff_sync(provider: str, new_voices: list[dict]) -> dict:
    existing = load_existing(provider)
    existing_by_id = {v["id"]: v for v in existing}
    new_by_id = {v["id"]: v for v in new_voices}
    now = _now()

    added, removed, updated, unchanged = [], [], [], []

    for vid, voice in new_by_id.items():
        if vid not in existing_by_id:
            voice["first_seen"] = voice["last_seen"] = now
            added.append(voice)
        else:
            old = existing_by_id[vid]
            voice["first_seen"] = old.get("first_seen", now)
            voice["last_seen"] = now
            if old.get("metadata_source") in _ENRICHED_SOURCES:
                for key in _ENRICHMENT_KEYS:
                    if old.get(key):
                        voice[key] = old[key]
            changed = any(old.get(k) != voice.get(k) for k in _PROVIDER_FIELDS)
            (updated if changed else unchanged).append(voice)
            if not changed:
                voice["last_synced"] = now

    for vid, old in existing_by_id.items():
        if vid not in new_by_id:
            old.update(status="deprecated", deprecated_at=now, last_seen=old.get("last_seen", now))
            removed.append(old)

    return {"added": added, "removed": removed, "updated": updated, "unchanged": unchanged}


def apply_sync(provider: str, new_voices: list[dict]) -> dict:
    result = diff_sync(provider, new_voices)
    all_voices = result["added"] + result["updated"] + result["unchanged"] + result["removed"]
    write_catalog(provider, all_voices)
    print(f"[{provider}] +{len(result['added'])} -{len(result['removed'])} ~{len(result['updated'])} ={len(result['unchanged'])} ({len(all_voices)} total)")
    return result


# ---------------------------------------------------------------------------
# Provider sync functions
# ---------------------------------------------------------------------------

RIME_LANG_MAP = {"eng": "en", "spa": "es", "fra": "fr", "ger": "de", "hin": "hi", "ara": "ar", "heb": "he", "jpn": "ja", "por": "pt"}


def sync_rime() -> list[dict]:
    resp = httpx.get("https://users.rime.ai/data/voices/all-v2.json", timeout=30)
    resp.raise_for_status()
    voices = []
    for model_family, languages in resp.json().items():
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
                    provider="rime", provider_voice_id=f"{model_family}:{n}",
                    name=n.replace("_", " ").title(), provider_model=model_family,
                    language=iso, provider_page_url="https://rime.ai",
                    provider_metadata={"model_family": model_family, "original_lang_code": lang_code},
                ))
    return voices


def sync_elevenlabs() -> list[dict]:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("[elevenlabs] No ELEVENLABS_API_KEY, skipping.")
        return []

    voices = []
    cursor = None
    with httpx.Client(timeout=30, headers={"xi-api-key": api_key}) as client:
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
                descriptive = v.get("descriptive", "")
                use_case = v.get("use_case", "")
                voices.append(make_voice(
                    provider="elevenlabs", provider_voice_id=vid, name=name_,
                    provider_model="eleven_turbo_v2_5",
                    description=f"{name_}. {descriptive}. {use_case}." if descriptive else name_,
                    gender=map_gender(v.get("gender")), age_group=map_age(v.get("age")),
                    accent=(v.get("accent", "") or "").lower() or None,
                    language=v.get("language", "en"),
                    style_tags=[t.strip().lower() for t in descriptive.split(",") if t.strip()] if descriptive else [],
                    use_cases=[u.strip().lower().replace(" ", "_") for u in use_case.split(",") if u.strip()] if use_case else [],
                    preview_url=v.get("preview_url"),
                    provider_page_url="https://elevenlabs.io/voice-library",
                ))
            cursor = data.get("last_sort_id")
            if not data.get("has_more", True) or not cursor:
                break
    return voices


def sync_deepgram() -> list[dict]:
    api_key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not api_key:
        print("[deepgram] No DEEPGRAM_API_KEY, skipping.")
        return []
    resp = httpx.get("https://api.deepgram.com/v1/models",
                     headers={"Authorization": f"Token {api_key}"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    voices = []
    for m in data.get("tts", []):
        vid = m.get("canonical_name", "")
        if not vid:
            continue
        name_ = m.get("name", vid).strip()
        langs = m.get("languages", [])
        lang = langs[0] if langs and isinstance(langs[0], str) else "en"
        if "-" in lang:
            lang = lang.split("-")[0]
        meta = m.get("metadata", {})
        model_family = "aura-2" if vid.startswith("aura-2") else "aura"
        sample_url = meta.get("sample") or None
        voices.append(make_voice(
            provider="deepgram", provider_voice_id=vid, name=name_,
            provider_model=model_family,
            gender=map_gender(meta.get("color")),  # Deepgram uses "color" for gender
            accent=meta.get("accent"),
            language=lang,
            preview_url=sample_url,
            provider_page_url="https://deepgram.com/product/text-to-speech",
            provider_metadata={"tags": meta.get("tags", []), "image": meta.get("image")},
        ))
    print(f"[deepgram] Fetched {len(voices)} voices from API")
    return voices


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


def sync_openai() -> list[dict]:
    return [make_voice(provider="openai", provider_voice_id=vid, name=n,
                       provider_model="gpt-4o-mini-tts", description=desc,
                       gender=g, age_group=a, accent=ac, language="en",
                       metadata_source="manual")
            for n, vid, g, a, ac, desc in OPENAI_VOICES]


def sync_cartesia() -> list[dict]:
    api_key = os.environ.get("CARTESIA_API_KEY", "")
    if not api_key:
        print("[cartesia] No CARTESIA_API_KEY, skipping.")
        return []
    resp = httpx.get("https://api.cartesia.ai/voices",
                     headers={"X-API-Key": api_key, "Cartesia-Version": "2024-06-10"}, timeout=30)
    resp.raise_for_status()
    voices = []
    for v in resp.json():
        vid, name_ = v.get("id", ""), v.get("name", "").strip()
        if not vid or not name_:
            continue
        lang = v.get("language", "en")
        if isinstance(lang, list):
            lang = lang[0] if lang else "en"
        voices.append(make_voice(provider="cartesia", provider_voice_id=vid, name=name_,
                                 description=v.get("description"), language=lang,
                                 provider_page_url="https://play.cartesia.ai"))
    return voices


def sync_playht() -> list[dict]:
    api_key = os.environ.get("PLAYHT_API_KEY", "")
    user_id = os.environ.get("PLAYHT_USER_ID", "")
    if not api_key or not user_id:
        print("[playht] No PLAYHT_API_KEY/PLAYHT_USER_ID, skipping.")
        return []
    resp = httpx.get("https://api.play.ht/api/v2/voices",
                     headers={"Authorization": f"Bearer {api_key}", "X-User-ID": user_id}, timeout=30)
    resp.raise_for_status()
    voices = []
    for v in resp.json():
        vid, name_ = v.get("id", ""), v.get("name", "").strip()
        if not vid or not name_:
            continue
        lang = (v.get("language_code", "en") or "en").split("-")[0]
        voices.append(make_voice(provider="playht", provider_voice_id=vid, name=name_,
                                 gender=map_gender(v.get("gender")), age_group=map_age(v.get("age")),
                                 accent=v.get("accent"), language=lang, texture=v.get("texture"),
                                 preview_url=v.get("sample"), provider_page_url="https://play.ht/voice-library"))
    return voices


PROVIDERS = {
    "elevenlabs": sync_elevenlabs, "rime": sync_rime, "deepgram": sync_deepgram,
    "openai": sync_openai, "cartesia": sync_cartesia, "playht": sync_playht,
}


def run_sync(providers: list[str] | None = None):
    targets = providers or list(PROVIDERS.keys())
    failed = False
    for name in targets:
        fn = PROVIDERS.get(name)
        if not fn:
            print(f"Unknown provider: {name}")
            continue
        try:
            print(f"\nSyncing {name}...")
            new_voices = fn()
            if new_voices:
                apply_sync(name, new_voices)
            else:
                print(f"[{name}] No voices returned")
        except Exception as e:
            print(f"[{name}] FAILED: {e}")
            traceback.print_exc()
            failed = True
    if failed:
        sys.exit(1)
