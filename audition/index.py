import asyncio
import os
from math import sqrt

from moss import DocumentInfo, MossClient, MutationOptions, QueryOptions

from audition.db import (cache_query_result, get_acoustic_features, get_embedding_rows,
                         get_cached_query, make_cache_key)
from audition.search import keyword_search, load_all_voices

_NAME_VIBES = {
    "bayou": "warm, southern, relaxed, earthy",
    "glacier": "cold, crisp, clear, precise",
    "alpine": "fresh, clean, bright, clear",
    "lotus": "calm, peaceful, meditative, serene",
    "breeze": "light, airy, gentle, relaxed",
    "canyon": "deep, resonant, powerful, echo",
    "ember": "warm, glowing, intimate, soft",
    "frost": "cool, sharp, precise, brisk",
    "harbor": "safe, steady, reliable, calm",
    "meadow": "gentle, natural, soft, warm",
    "sage": "wise, calm, mature, thoughtful",
    "willow": "graceful, flowing, gentle, soft",
    "cedar": "grounded, steady, warm, reliable",
    "coral": "bright, warm, friendly, engaging",
    "nova": "bright, energetic, fresh, dynamic",
    "onyx": "deep, powerful, commanding, premium",
    "dusk": "calm, mellow, reflective, warm",
    "dawn": "fresh, hopeful, bright, optimistic",
    "vale": "peaceful, gentle, quiet, calm",
    "ridge": "strong, clear, rugged, assertive",
    "brook": "flowing, light, cheerful, gentle",
    "flint": "sharp, decisive, direct",
    "moss": "soft, earthy, quiet, understated",
    "rain": "soothing, steady, calming",
    "storm": "powerful, dramatic, commanding",
    "pearl": "refined, smooth, elegant",
    "oak": "strong, deep, reliable, trustworthy",
    "cove": "sheltered, intimate, calm, safe",
    "summit": "commanding, clear, high",
}

_DEEPGRAM_VIBES = {
    "thalia": "cheerful, warm, lighthearted",
    "andromeda": "bold, adventurous, spirited",
    "athena": "wise, authoritative, composed",
    "atlas": "strong, reliable, powerful",
    "helios": "radiant, warm, commanding",
    "hera": "queenly, authoritative, dignified",
    "luna": "soft, gentle, dreamy, calming",
    "orion": "bold, adventurous, commanding",
    "perseus": "heroic, young, confident",
    "zeus": "commanding, powerful, deep",
    "apollo": "golden, harmonious, refined",
    "echo": "resonant, clear, memorable",
    "harmony": "balanced, musical, pleasant",
    "hermes": "quick, clever, youthful",
    "orpheus": "musical, enchanting, captivating",
    "phoenix": "dynamic, energetic, transformative",
    "selene": "lunar, calm, serene, luminous",
    "vesta": "warm, nurturing, steady",
}


def _trait_label(value: float) -> str:
    if value < 0.3:
        return "low"
    if value <= 0.7:
        return "moderate"
    return "high"


def voice_to_document(voice: dict) -> DocumentInfo:
    name = voice.get("name", "")
    provider = voice.get("provider", "")
    gender = voice.get("gender")
    age_group = voice.get("age_group")
    accent = voice.get("accent")
    description = voice.get("description") or ""
    traits = voice.get("traits") or {}

    parts = []
    identity = f"{name} is a"
    if gender and gender != "unknown":
        identity += f" {gender}"
    identity += f" voice from {provider}"
    if voice.get("provider_model"):
        identity += f" ({voice['provider_model']})"
    identity += "."
    if age_group and age_group != "unknown":
        identity += f" {age_group.capitalize()}-aged."
    if accent:
        identity += f" {accent.capitalize()} accent."
    parts.append(identity)

    if description and len(description) > 20:
        parts.append(description)
    else:
        name_lower = name.lower().replace(" ", "").replace("_", "")
        if provider == "deepgram":
            vibes = _DEEPGRAM_VIBES.get(name_lower)
            if vibes:
                parts.append(f"Voice character: {vibes}.")
        for hint_name, vibes in _NAME_VIBES.items():
            if hint_name in name_lower:
                parts.append(f"Name evokes: {vibes}.")
                break

    for key, label in [("personality_tags", "Personality"), ("use_cases", "Best for"), ("style_tags", "Style")]:
        values = voice.get(key) or []
        if values:
            parts.append(f"{label}: {', '.join(values)}.")

    trait_bits = []
    for key in ("warmth", "energy", "clarity", "authority", "friendliness", "confidence"):
        value = traits.get(key)
        if value is not None:
            trait_bits.append(f"{_trait_label(value)} {key}")
    if trait_bits:
        parts.append(f"{', '.join(trait_bits).capitalize()}.")

    text = " ".join(parts)

    metadata: dict[str, str] = {}
    if provider:
        metadata["provider"] = provider
    if gender and gender != "unknown":
        metadata["gender"] = gender
    if age_group and age_group != "unknown":
        metadata["age_group"] = age_group
    if accent:
        metadata["accent"] = accent.lower()

    voice_id = voice.get("id", f"{provider}:{voice.get('provider_voice_id', name)}")
    return DocumentInfo(id=voice_id, text=text, metadata=metadata)


async def build_index(force: bool = False, changed_ids: set[str] | None = None) -> None:
    project_id = os.environ.get("MOSS_PROJECT_ID")
    project_key = os.environ.get("MOSS_PROJECT_KEY")
    if not project_id or not project_key:
        print("[index] MOSS_PROJECT_ID and MOSS_PROJECT_KEY required.")
        return

    voices = load_all_voices()
    if not voices:
        print("[index] No voices in catalog.")
        return

    seen = set()
    documents = []
    for voice in voices:
        doc = voice_to_document(voice)
        if doc.id not in seen:
            seen.add(doc.id)
            documents.append(doc)

    client = MossClient(project_id, project_key)

    if changed_ids and not force:
        try:
            await client.get_index("voice-audition")
        except Exception:
            changed_ids = None

    if changed_ids and not force:
        diff_docs = [doc for doc in documents if doc.id in changed_ids]
        if not diff_docs:
            print("[index] No changed documents to upsert.")
            return
        print(f"[index] Upserting {len(diff_docs)} changed voices (of {len(documents)} total)...")
        await client.add_docs("voice-audition", diff_docs, MutationOptions(upsert=True))
    else:
        print(f"[index] Full rebuild: {len(documents)} voices...")
        try:
            await client.delete_index("voice-audition")
        except Exception:
            pass
        await client.create_index("voice-audition", documents, "moss-minilm")

    print("[index] Done.")


async def semantic_search(query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
    project_id = os.environ.get("MOSS_PROJECT_ID")
    project_key = os.environ.get("MOSS_PROJECT_KEY")
    if not project_id or not project_key:
        return []

    client = MossClient(project_id, project_key)
    await client.load_index("voice-audition")

    moss_filter = None
    if filters:
        moss_filter = {"$and": [{"field": key, "condition": {"$eq": value}} for key, value in filters.items()]}

    result = await client.query("voice-audition", query, QueryOptions(top_k=top_k, alpha=0.7, filter=moss_filter))
    return [{"id": doc.id, "text": doc.text, "score": doc.score, "metadata": doc.metadata} for doc in result.docs]


def search_voices(query: str, top_k: int = 5, filters: dict | None = None) -> dict:
    cache_key = make_cache_key("search", {"query": query.strip().lower(), "top_k": top_k, "filters": filters or {}})
    cached = get_cached_query(cache_key, "search")
    if cached is not None:
        return {"mode": cached["mode"], "results": cached["results"], "cache_hit": True}

    mode = "semantic"
    try:
        results = asyncio.run(semantic_search(query, top_k=top_k, filters=filters))
    except Exception:
        results = []
    if not results:
        mode = "keyword"
        results = keyword_search(query, top_k=top_k, filters=filters)
    payload = {"mode": mode, "results": results}
    cache_query_result(cache_key, "search", payload)
    return {"mode": mode, "results": results, "cache_hit": False}


def run_index(force: bool = False, changed_ids: set[str] | None = None):
    asyncio.run(build_index(force=force, changed_ids=changed_ids))


def run_semantic_search(query: str, top_k: int = 5):
    outcome = search_voices(query, top_k=top_k)
    mode = outcome["mode"]
    results = outcome["results"]
    if mode == "keyword":
        print("[search] Semantic search unavailable, using local keyword mode.")

    print(f'Search ({mode}): "{query}" ({len(results)} results)\n')
    voice_map = {voice["id"]: voice for voice in load_all_voices()}
    for result in results:
        meta = result.get("metadata", {})
        if meta:
            voice = voice_map.get(result.get("id", ""), {})
            labels = [meta.get(key, "") for key in ("gender", "age_group", "accent") if meta.get(key)]
            doc_id = result.get("id", "")
            name = doc_id.split(":", 1)[1] if ":" in doc_id else doc_id
            print(
                f"  {result.get('score', 0):.3f}  {name} ({meta.get('provider', '')}) "
                f"[{', '.join(labels)}] cost={voice.get('effective_cost_per_min_usd')}"
            )
            sentences = result.get("text", "").split(". ")
            if len(sentences) > 1:
                print(f"         {sentences[1].rstrip('.')}")
        else:
            labels = [result.get(key, "") for key in ("gender", "age_group", "accent") if result.get(key)]
            print(
                f"  {result.get('score', 0):.3f}  {result.get('name', '')} ({result.get('provider', '')}) "
                f"[{', '.join(labels)}] cost={result.get('effective_cost_per_min_usd')}"
            )
            if result.get("description"):
                print(f"         {result['description']}")
        print()


def search_similar_voices(voice_id: str, top_k: int = 5) -> list[dict]:
    target = None
    for candidate_id, vector in get_embedding_rows():
        if candidate_id == voice_id:
            target = vector
            break
    if target is None:
        return []

    voices = {voice["id"]: voice for voice in load_all_voices()}
    scored = []
    target_norm = sqrt(sum(value * value for value in target)) or 1.0
    for candidate_id, vector in get_embedding_rows():
        if candidate_id == voice_id:
            continue
        denom = (sqrt(sum(value * value for value in vector)) or 1.0) * target_norm
        score = sum(a * b for a, b in zip(target, vector)) / denom
        voice = voices.get(candidate_id)
        if voice:
            scored.append((score, voice))
    scored.sort(key=lambda item: -item[0])
    return [{**voice, "score": round(score, 4)} for score, voice in scored[:top_k]]


def acoustic_profile_summary(voice_id: str) -> dict | None:
    features = get_acoustic_features(voice_id)
    if not features:
        return None
    notes = []
    f0 = features.get("f0_mean_hz")
    if f0 is not None:
        notes.append(f"mean pitch {f0:.1f} Hz")
    rate = features.get("speech_rate_syl_per_sec")
    if rate is not None:
        notes.append(f"speech rate {rate:.2f} syllables/s")
    hnr = features.get("hnr_db")
    if hnr is not None:
        notes.append(f"HNR {hnr:.2f} dB")
    return {**features, "summary": ", ".join(notes)}
