import asyncio
import os

from moss import DocumentInfo, MossClient, QueryOptions

from audition.search import load_all_voices

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

    # Identity
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

    # Description or name vibes
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
        vals = voice.get(key) or []
        if vals:
            parts.append(f"{label}: {', '.join(vals)}.")

    # Traits
    trait_bits = []
    for k in ("warmth", "energy", "clarity", "authority", "friendliness", "confidence"):
        val = traits.get(k)
        if val is not None:
            trait_bits.append(f"{_trait_label(val)} {k}")
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


async def build_index(force: bool = False) -> None:
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
    for v in voices:
        doc = voice_to_document(v)
        if doc.id not in seen:
            seen.add(doc.id)
            documents.append(doc)

    print(f"[index] Indexing {len(documents)} voices...")
    client = MossClient(project_id, project_key)
    try:
        await client.delete_index("voice-audition")
    except Exception:
        pass
    await client.create_index("voice-audition", documents, "moss-minilm")
    print(f"[index] Done.")


async def semantic_search(query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
    project_id = os.environ.get("MOSS_PROJECT_ID")
    project_key = os.environ.get("MOSS_PROJECT_KEY")
    if not project_id or not project_key:
        return []

    client = MossClient(project_id, project_key)
    await client.load_index("voice-audition")

    moss_filter = None
    if filters:
        moss_filter = {"$and": [{"field": f, "condition": {"$eq": v}} for f, v in filters.items()]}

    result = await client.query("voice-audition", query, QueryOptions(top_k=top_k, alpha=0.7, filter=moss_filter))
    return [{"id": d.id, "text": d.text, "score": d.score, "metadata": d.metadata} for d in result.docs]


def run_index(force: bool = False):
    asyncio.run(build_index(force=force))


def run_semantic_search(query: str, top_k: int = 5):
    results = asyncio.run(semantic_search(query, top_k=top_k))
    print(f'Search: "{query}" ({len(results)} results)\n')
    for r in results:
        meta = r.get("metadata", {})
        labels = [meta.get(k, "") for k in ("gender", "age_group", "accent") if meta.get(k)]
        doc_id = r.get("id", "")
        name = doc_id.split(":", 1)[1] if ":" in doc_id else doc_id
        print(f"  {r.get('score', 0):.3f}  {name} ({meta.get('provider', '')}) [{', '.join(labels)}]")
        sentences = r.get("text", "").split(". ")
        if len(sentences) > 1:
            print(f"         {sentences[1].rstrip('.')}")
        print()
