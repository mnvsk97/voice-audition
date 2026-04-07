import os
import traceback
from datetime import datetime, timezone

import httpx

from audition.db import (import_hosting_catalog, import_provider_catalog, load_voices,
                         normalize_voice, record_provider_sync_run, upsert_voices)
from audition.schema import make_voice


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_existing(provider: str) -> list[dict]:
    return load_voices(provider=provider, include_deprecated=True)


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


def _env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def _azure_style_tags(styles: list[str] | None) -> list[str]:
    if not styles:
        return []
    mapped = set()
    for style in styles:
        s = (style or "").strip().lower()
        if s in {"assistant", "chat", "customerservice", "friendly"}:
            mapped.add("conversational")
        elif s in {"newscast", "serious"}:
            mapped.add("formal")
        elif s in {"cheerful", "excited", "hopeful"}:
            mapped.add("upbeat")
        elif s in {"angry", "terrified", "unfriendly", "disgruntled", "sad", "depressed"}:
            mapped.add("dramatic")
        elif s in {"whispering", "calm"}:
            mapped.add("soothing")
        elif s in {"narration-relaxed"}:
            mapped.add("relaxed")
        elif s in {"narration-professional"}:
            mapped.add("articulate")
    return sorted(mapped)


def _azure_use_cases(roleplay: list[str] | None) -> list[str]:
    if not roleplay:
        return []
    mapped = set()
    for role in roleplay:
        r = (role or "").strip().lower()
        if r == "narrator":
            mapped.add("storytelling")
        elif r == "assistant":
            mapped.add("assistant")
        elif r == "customerservice":
            mapped.add("customer_support")
    return sorted(mapped)


def _google_model_from_name(name: str | None) -> str | None:
    if not name:
        return None
    parts = name.split("-")
    if len(parts) >= 3:
        return parts[2]
    return None


_ENRICHMENT_KEYS = (
    "description", "gender", "age_group", "accent", "traits", "texture", "pitch",
    "personality_tags", "style_tags", "use_cases", "enrichment", "metadata_source",
    "enrichment_status", "enrichment_attempts",
)
_ENRICHED_SOURCES = ("enriched_local", "enriched_cloud", "manual", "hybrid")
_PROVIDER_FIELDS = (
    "name", "provider_model", "preview_url", "provider_page_url", "provider_metadata",
    "effective_cost_per_min_usd", "effective_latency_tier",
)


def diff_sync(provider: str, new_voices: list[dict]) -> dict:
    existing = load_existing(provider)
    existing_by_id = {voice["id"]: voice for voice in existing}
    new_by_id = {voice["id"]: voice for voice in new_voices}
    now = _now()

    added, removed, updated, unchanged = [], [], [], []

    for voice_id, voice in new_by_id.items():
        if voice_id not in existing_by_id:
            voice["first_seen"] = voice["last_seen"] = now
            added.append(voice)
            continue

        old = existing_by_id[voice_id]
        voice["first_seen"] = old.get("first_seen", now)
        voice["last_seen"] = now
        if old.get("metadata_source") in _ENRICHED_SOURCES:
            for key in _ENRICHMENT_KEYS:
                if old.get(key):
                    voice[key] = old[key]

        old_normalized = normalize_voice(old)
        new_normalized = normalize_voice(voice)
        changed = any(old_normalized.get(key) != new_normalized.get(key) for key in _PROVIDER_FIELDS)
        if changed:
            updated.append(voice)
        else:
            voice["last_synced"] = now
            unchanged.append(voice)

    for voice_id, old in existing_by_id.items():
        if voice_id not in new_by_id:
            old.update(status="deprecated", deprecated_at=now, last_seen=old.get("last_seen", now))
            removed.append(old)

    return {"added": added, "removed": removed, "updated": updated, "unchanged": unchanged}


def apply_sync(provider: str, new_voices: list[dict]) -> dict:
    result = diff_sync(provider, new_voices)
    all_voices = result["added"] + result["updated"] + result["unchanged"] + result["removed"]
    upsert_voices(all_voices)
    print(f"[{provider}] +{len(result['added'])} -{len(result['removed'])} ~{len(result['updated'])} ={len(result['unchanged'])} ({len(all_voices)} total)")
    return result


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
            for name in names:
                if not isinstance(name, str) or not name.strip():
                    continue
                voices.append(make_voice(
                    provider="rime", provider_voice_id=f"{model_family}:{name}",
                    name=name.replace("_", " ").title(), provider_model=model_family,
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
            for voice in batch:
                voice_id = voice.get("voice_id", "")
                name = voice.get("name", "").strip()
                if not voice_id or not name:
                    continue
                descriptive = voice.get("descriptive", "")
                use_case = voice.get("use_case", "")
                voices.append(make_voice(
                    provider="elevenlabs", provider_voice_id=voice_id, name=name,
                    provider_model="eleven_turbo_v2_5",
                    description=f"{name}. {descriptive}. {use_case}." if descriptive else name,
                    gender=map_gender(voice.get("gender")), age_group=map_age(voice.get("age")),
                    accent=(voice.get("accent", "") or "").lower() or None,
                    language=voice.get("language", "en"),
                    style_tags=[tag.strip().lower() for tag in descriptive.split(",") if tag.strip()] if descriptive else [],
                    use_cases=[item.strip().lower().replace(" ", "_") for item in use_case.split(",") if item.strip()] if use_case else [],
                    preview_url=voice.get("preview_url"),
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
    resp = httpx.get(
        "https://api.deepgram.com/v1/models",
        headers={"Authorization": f"Token {api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    voices = []
    for model in data.get("tts", []):
        voice_id = model.get("canonical_name", "")
        if not voice_id:
            continue
        name = model.get("name", voice_id).strip()
        languages = model.get("languages", [])
        language = languages[0] if languages and isinstance(languages[0], str) else "en"
        if "-" in language:
            language = language.split("-")[0]
        meta = model.get("metadata", {})
        model_family = "aura-2" if voice_id.startswith("aura-2") else "aura"
        sample_url = meta.get("sample") or None
        voices.append(make_voice(
            provider="deepgram", provider_voice_id=voice_id, name=name,
            provider_model=model_family,
            gender=map_gender(meta.get("color")),
            accent=meta.get("accent"),
            language=language,
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
    return [
        make_voice(
            provider="openai",
            provider_voice_id=voice_id,
            name=name,
            provider_model="gpt-4o-mini-tts",
            description=description,
            gender=gender,
            age_group=age_group,
            accent=accent,
            language="en",
            metadata_source="manual",
        )
        for name, voice_id, gender, age_group, accent, description in OPENAI_VOICES
    ]


def sync_cartesia() -> list[dict]:
    api_key = os.environ.get("CARTESIA_API_KEY", "")
    if not api_key:
        print("[cartesia] No CARTESIA_API_KEY, skipping.")
        return []
    resp = httpx.get(
        "https://api.cartesia.ai/voices",
        headers={"X-API-Key": api_key, "Cartesia-Version": "2024-06-10"},
        timeout=30,
    )
    resp.raise_for_status()
    voices = []
    for voice in resp.json():
        voice_id = voice.get("id", "")
        name = voice.get("name", "").strip()
        if not voice_id or not name:
            continue
        language = voice.get("language", "en")
        if isinstance(language, list):
            language = language[0] if language else "en"
        voices.append(make_voice(
            provider="cartesia",
            provider_voice_id=voice_id,
            name=name,
            description=voice.get("description"),
            language=language,
            provider_page_url="https://play.cartesia.ai",
        ))
    return voices


def sync_azure() -> list[dict]:
    api_key = _env("AZURE_SPEECH_KEY", "AZURE_SPEECH_SUBSCRIPTION_KEY")
    region = _env("AZURE_SPEECH_REGION", "AZURE_REGION")
    if not api_key or not region:
        print("[azure] No AZURE_SPEECH_KEY/AZURE_SPEECH_REGION, skipping.")
        return []

    resp = httpx.get(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list",
        headers={"Ocp-Apim-Subscription-Key": api_key},
        timeout=30,
    )
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        print("[azure] Unexpected response shape, skipping.")
        return []

    voices = []
    for voice in data:
        if not isinstance(voice, dict):
            continue
        short_name = (voice.get("ShortName") or "").strip()
        if not short_name:
            continue
        display_name = (voice.get("DisplayName") or voice.get("LocalName") or short_name).strip()
        locale = (voice.get("Locale") or "en").strip()
        language = locale.split("-")[0] if locale else "en"
        voices.append(make_voice(
            provider="azure",
            provider_voice_id=short_name,
            name=display_name,
            provider_model=(voice.get("VoiceType") or None),
            gender=map_gender(voice.get("Gender")),
            language=language,
            additional_languages=[lang for lang in voice.get("SecondaryLocaleList", []) if isinstance(lang, str)],
            style_tags=_azure_style_tags(voice.get("StyleList")),
            use_cases=_azure_use_cases(voice.get("RolePlayList")),
            provider_page_url="https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech",
            provider_metadata={
                "name": voice.get("Name"),
                "display_name": voice.get("DisplayName"),
                "local_name": voice.get("LocalName"),
                "locale_name": voice.get("LocaleName"),
                "sample_rate_hertz": voice.get("SampleRateHertz"),
                "status": voice.get("Status"),
                "words_per_minute": voice.get("WordsPerMinute"),
                "style_list": voice.get("StyleList", []),
                "role_play_list": voice.get("RolePlayList", []),
                "extended_property_map": voice.get("ExtendedPropertyMap", {}),
            },
        ))
    print(f"[azure] Fetched {len(voices)} voices from API")
    return voices


def sync_google() -> list[dict]:
    access_token = _env("GOOGLE_ACCESS_TOKEN", "GOOGLE_OAUTH_ACCESS_TOKEN")
    if not access_token:
        print("[google] No GOOGLE_ACCESS_TOKEN/GOOGLE_OAUTH_ACCESS_TOKEN, skipping.")
        return []

    resp = httpx.get(
        "https://texttospeech.googleapis.com/v1/voices",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    resp.raise_for_status()

    data = resp.json()
    voices_raw = data.get("voices", []) if isinstance(data, dict) else data
    if not isinstance(voices_raw, list):
        print("[google] Unexpected response shape, skipping.")
        return []

    voices = []
    for voice in voices_raw:
        if not isinstance(voice, dict):
            continue
        name = (voice.get("name") or "").strip()
        if not name:
            continue
        languages = [lang for lang in voice.get("languageCodes", []) if isinstance(lang, str)]
        language = languages[0] if languages else "en"
        voices.append(make_voice(
            provider="google",
            provider_voice_id=name,
            name=name,
            provider_model=_google_model_from_name(name),
            gender=map_gender(voice.get("ssmlGender")),
            language=language,
            additional_languages=languages[1:] if len(languages) > 1 else [],
            provider_page_url="https://cloud.google.com/text-to-speech",
            provider_metadata={
                "name": name,
                "language_codes": languages,
                "natural_sample_rate_hertz": voice.get("naturalSampleRateHertz"),
                "ssml_gender": voice.get("ssmlGender"),
                "raw": voice,
            },
        ))
    print(f"[google] Fetched {len(voices)} voices from API")
    return voices


def sync_playht() -> list[dict]:
    api_key = os.environ.get("PLAYHT_API_KEY", "")
    user_id = os.environ.get("PLAYHT_USER_ID", "")
    if not api_key or not user_id:
        print("[playht] No PLAYHT_API_KEY/PLAYHT_USER_ID, skipping.")
        return []
    resp = httpx.get(
        "https://api.play.ht/api/v2/voices",
        headers={"Authorization": f"Bearer {api_key}", "X-User-ID": user_id},
        timeout=30,
    )
    resp.raise_for_status()
    voices = []
    for voice in resp.json():
        voice_id = voice.get("id", "")
        name = voice.get("name", "").strip()
        if not voice_id or not name:
            continue
        language = (voice.get("language_code", "en") or "en").split("-")[0]
        voices.append(make_voice(
            provider="playht",
            provider_voice_id=voice_id,
            name=name,
            gender=map_gender(voice.get("gender")),
            age_group=map_age(voice.get("age")),
            accent=voice.get("accent"),
            language=language,
            texture=voice.get("texture"),
            preview_url=voice.get("sample"),
            provider_page_url="https://play.ht/voice-library",
        ))
    return voices


PROVIDERS = {
    "elevenlabs": sync_elevenlabs,
    "rime": sync_rime,
    "deepgram": sync_deepgram,
    "openai": sync_openai,
    "cartesia": sync_cartesia,
    "playht": sync_playht,
    "azure": sync_azure,
    "google": sync_google,
}


def run_sync(providers: list[str] | None = None) -> dict:
    import_provider_catalog()
    import_hosting_catalog()
    targets = providers or list(PROVIDERS.keys())
    synced, errors = [], []
    for name in targets:
        fn = PROVIDERS.get(name)
        if not fn:
            print(f"Unknown provider: {name}")
            continue
        try:
            print(f"\nSyncing {name}...")
            new_voices = fn()
            if new_voices:
                result = apply_sync(name, new_voices)
                total = len(result["added"]) + len(result["updated"]) + len(result["unchanged"]) + len(result["removed"])
                record_provider_sync_run(
                    name,
                    "completed",
                    added_count=len(result["added"]),
                    updated_count=len(result["updated"]),
                    removed_count=len(result["removed"]),
                    total_count=total,
                    finished_at=_now(),
                )
                synced.append(
                    {
                        "provider": name,
                        "added": len(result["added"]),
                        "removed": len(result["removed"]),
                        "updated": len(result["updated"]),
                        "total": total,
                    }
                )
            else:
                print(f"[{name}] No voices returned")
        except Exception as exc:
            print(f"[{name}] FAILED: {exc}")
            traceback.print_exc()
            record_provider_sync_run(name, "failed", error=str(exc), finished_at=_now())
            errors.append({"provider": name, "error": str(exc)})
    return {"synced": synced, "errors": errors}
