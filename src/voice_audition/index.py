import asyncio
import os

from moss import DocumentInfo, MossClient, QueryOptions

from voice_audition.search import load_all_voices


def _trait_label(value: float) -> str:
    if value < 0.3:
        return "low"
    elif value <= 0.7:
        return "moderate"
    else:
        return "high"


_NAME_VIBES = {
    # Rime evocative names
    "bayou": "warm, southern, relaxed, swampy, earthy",
    "glacier": "cold, crisp, clear, icy, precise",
    "alpine": "fresh, clean, bright, outdoorsy, clear",
    "lotus": "calm, peaceful, zen, meditative, serene",
    "breeze": "light, airy, gentle, easy, relaxed",
    "canyon": "deep, resonant, vast, powerful, echo",
    "ember": "warm, glowing, intimate, cozy, soft",
    "frost": "cool, sharp, precise, clear, brisk",
    "harbor": "safe, steady, reliable, welcoming, calm",
    "meadow": "gentle, natural, soft, pastoral, warm",
    "pebble": "small, clear, precise, light, gentle",
    "sage": "wise, calm, knowing, mature, thoughtful",
    "willow": "graceful, flowing, gentle, flexible, soft",
    "cedar": "grounded, steady, warm, natural, reliable",
    "coral": "bright, warm, friendly, colorful, engaging",
    "nova": "bright, new, energetic, fresh, dynamic",
    "onyx": "deep, dark, powerful, commanding, premium",
    "dusk": "calm, winding down, mellow, reflective, warm",
    "dawn": "fresh, hopeful, new, bright, optimistic",
    "vale": "peaceful, sheltered, gentle, quiet, calm",
    "ridge": "strong, defined, clear, rugged, assertive",
    "brook": "flowing, light, cheerful, natural, gentle",
    "flint": "sharp, strong, decisive, no-nonsense, direct",
    "moss": "soft, earthy, quiet, natural, understated",
    "rain": "soothing, cleansing, steady, calming, natural",
    "storm": "powerful, dramatic, intense, commanding, dynamic",
    "pearl": "refined, smooth, elegant, polished, precious",
    "ivy": "classic, enduring, refined, growing, green",
    "reed": "thin, flexible, natural, light, gentle",
    "blossom": "blooming, fresh, sweet, gentle, spring",
    "petal": "delicate, soft, gentle, feminine, light",
    "thorn": "sharp, edgy, protective, bold, direct",
    "oak": "strong, deep, reliable, rooted, trustworthy",
    "birch": "light, elegant, clean, slender, bright",
    "cove": "sheltered, intimate, calm, private, safe",
    "delta": "flowing, change, broad, expansive, warm",
    "summit": "peak, commanding, achieved, clear, high",
    "dune": "warm, shifting, sandy, desert, dry",
}

_DEEPGRAM_VIBES = {
    "thalia": "muse of comedy, cheerful, warm, lighthearted, entertaining",
    "andromeda": "bright, celestial, bold, adventurous, spirited",
    "arcas": "strong, bear-like, protective, steady, grounded",
    "asteria": "starry, celestial, bright, clear, luminous",
    "athena": "wise, strategic, authoritative, intelligent, composed",
    "atlas": "strong, enduring, reliable, supporting, powerful",
    "helios": "radiant, warm, bright, commanding, solar",
    "hera": "queenly, authoritative, mature, dignified, powerful",
    "luna": "soft, luminous, gentle, dreamy, calming",
    "orion": "bold, strong, adventurous, clear, commanding",
    "perseus": "heroic, brave, young, dynamic, confident",
    "stella": "starry, bright, clear, elegant, shining",
    "zeus": "commanding, powerful, authoritative, deep, thunderous",
    "angus": "warm, celtic, strong, earthy, friendly",
    "apollo": "golden, harmonious, artistic, refined, bright",
    "cora": "maiden, gentle, fresh, sweet, approachable",
    "daphne": "graceful, natural, flowing, elegant, classical",
    "echo": "resonant, reflective, clear, repeating, memorable",
    "electra": "electric, bright, energetic, sharp, vivid",
    "harmony": "balanced, musical, pleasant, agreeable, smooth",
    "helena": "beautiful, classic, warm, gracious, elegant",
    "hercules": "powerful, strong, heroic, deep, commanding",
    "hermes": "quick, clever, messenger, agile, youthful",
    "iris": "colorful, rainbow, bright, connecting, gentle",
    "jason": "adventurous, leader, bold, determined, capable",
    "juno": "regal, protective, mature, authoritative, nurturing",
    "leda": "graceful, mythical, gentle, elegant, serene",
    "lyra": "musical, lyrical, melodic, artistic, beautiful",
    "minerva": "wise, scholarly, mature, knowledgeable, composed",
    "neptune": "deep, oceanic, powerful, commanding, vast",
    "odysseus": "experienced, storytelling, wise, weathered, journeyed",
    "ophelia": "gentle, emotional, poetic, delicate, expressive",
    "orpheus": "musical, enchanting, emotional, artistic, captivating",
    "pandora": "curious, alluring, mysterious, complex, engaging",
    "phoenix": "rising, dynamic, transformative, energetic, reborn",
    "poseidon": "deep, powerful, oceanic, commanding, vast",
    "selene": "lunar, calm, serene, gentle, luminous",
    "titan": "massive, powerful, imposing, strong, commanding",
    "triton": "oceanic, trumpeting, bold, youthful, messenger",
    "vesta": "hearth, warm, nurturing, domestic, steady",
}


def voice_to_document(voice: dict) -> DocumentInfo:
    """Convert a voice catalog entry to a Moss DocumentInfo."""
    name = voice.get("name", "")
    provider = voice.get("provider", "")
    gender = voice.get("gender")
    age_group = voice.get("age_group")
    accent = voice.get("accent")
    language = voice.get("language")
    provider_model = voice.get("provider_model")
    description = voice.get("description") or ""
    use_cases = voice.get("use_cases") or []
    personality_tags = voice.get("personality_tags") or []
    style_tags = voice.get("style_tags") or []
    traits = voice.get("traits") or {}
    texture = voice.get("texture")
    pitch = voice.get("pitch")
    speaking_style = voice.get("speaking_style")
    latency_tier = voice.get("latency_tier")
    cost_per_min_usd = voice.get("cost_per_min_usd")
    pipecat_supported = voice.get("pipecat_supported", False)

    parts = []

    # Identity line
    identity = f"{name} is a"
    if gender and gender != "unknown":
        identity += f" {gender}"
    identity += f" voice from {provider}"
    if provider_model:
        identity += f" using the {provider_model} model"
    identity += "."

    # Age / accent
    qualifiers = []
    if age_group and age_group != "unknown":
        qualifiers.append(f"{age_group.capitalize()}-aged")
    if accent:
        qualifiers.append(f"with an {accent.capitalize()} accent")
    if qualifiers:
        identity += " " + " ".join(qualifiers) + "."

    if language:
        identity += f" {language.upper()} language." if len(language) <= 3 else f" {language} language."

    parts.append(identity)

    if description and len(description) > 20:
        parts.append(description)
    else:
        name_lower = name.lower().replace(" ", "").replace("_", "")
        # Check Deepgram mythology names
        if provider == "deepgram":
            vibes = _DEEPGRAM_VIBES.get(name_lower)
            if vibes:
                parts.append(f"Voice character: {vibes}.")
        # Check evocative name hints (Rime and others)
        for hint_name, vibes in _NAME_VIBES.items():
            if hint_name in name_lower:
                parts.append(f"Name evokes: {vibes}.")
                break

    if personality_tags:
        parts.append(f"Personality: {', '.join(personality_tags)}.")

    if use_cases:
        parts.append(f"Best for: {', '.join(use_cases)}.")

    if style_tags:
        parts.append(f"Style: {', '.join(style_tags)}.")

    # Voice quality
    quality_bits = []
    if texture:
        quality_bits.append(f"{texture} texture")
    if pitch:
        quality_bits.append(f"{pitch} pitch")
    if speaking_style:
        quality_bits.append(f"{speaking_style} style")
    if quality_bits:
        parts.append(f"{', '.join(quality_bits).capitalize()}.")

    # Traits
    trait_bits = []
    for key in ("warmth", "energy", "clarity", "authority", "friendliness",
                "confidence", "expressiveness", "pace"):
        val = traits.get(key)
        if val is not None:
            trait_bits.append(f"{_trait_label(val)} {key}")
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
    if language:
        metadata["language"] = language
    if latency_tier:
        metadata["latency_tier"] = latency_tier
    if cost_per_min_usd is not None:
        metadata["cost_per_min_usd"] = str(cost_per_min_usd)
    metadata["pipecat_supported"] = str(bool(pipecat_supported)).lower()
    metadata["has_description"] = str(bool(description)).lower()

    voice_id = voice.get("id", f"{provider}:{voice.get('provider_voice_id', name)}")

    return DocumentInfo(id=voice_id, text=text, metadata=metadata)


async def build_index(force: bool = False) -> None:
    """Build the Moss semantic index from the voice catalog."""
    project_id = os.environ.get("MOSS_PROJECT_ID")
    project_key = os.environ.get("MOSS_PROJECT_KEY")
    if not project_id or not project_key:
        print("[index] Error: MOSS_PROJECT_ID and MOSS_PROJECT_KEY env vars are required.")
        return

    voices = load_all_voices()
    if not voices:
        print("[index] No voices found in catalog.")
        return

    seen = set()
    documents = []
    for v in voices:
        doc = voice_to_document(v)
        if doc.id not in seen:
            seen.add(doc.id)
            documents.append(doc)
    n = len(documents)
    print(f"[index] Indexing {n} voices ({len(voices) - n} duplicates removed)...")

    client = MossClient(project_id, project_key)
    await client.create_index("voice-audition", documents, "moss-minilm")

    print(f"[index] Done. Indexed {n} voices in Moss.")


async def semantic_search(
    query: str,
    top_k: int = 5,
    filters: dict | None = None,
) -> list[dict]:
    """Run hybrid semantic + keyword search over the voice index."""
    project_id = os.environ.get("MOSS_PROJECT_ID")
    project_key = os.environ.get("MOSS_PROJECT_KEY")
    if not project_id or not project_key:
        print("[search] Error: MOSS_PROJECT_ID and MOSS_PROJECT_KEY env vars are required.")
        return []

    client = MossClient(project_id, project_key)
    await client.load_index("voice-audition")

    moss_filter = None
    if filters:
        conditions = [
            {"field": field, "condition": {"$eq": value}}
            for field, value in filters.items()
        ]
        moss_filter = {"$and": conditions}

    result = await client.query(
        "voice-audition",
        query,
        QueryOptions(top_k=top_k, alpha=0.7, filter=moss_filter),
    )

    return [
        {
            "id": doc.id,
            "text": doc.text,
            "score": doc.score,
            "metadata": doc.metadata,
        }
        for doc in result.docs
    ]


def run_index(force: bool = False) -> None:
    asyncio.run(build_index(force=force))


def run_semantic_search(query: str, top_k: int = 5) -> None:
    results = asyncio.run(semantic_search(query, top_k=top_k))
    n = len(results)
    print(f'Search: "{query}" ({n} results)')
    print()
    for r in results:
        meta = r.get("metadata", {})
        labels = []
        if meta.get("gender"):
            labels.append(meta["gender"])
        if meta.get("age_group"):
            labels.append(meta["age_group"])
        if meta.get("accent"):
            labels.append(meta["accent"])
        label_str = f" [{', '.join(labels)}]" if labels else ""

        doc_id = r.get("id", "")
        provider = meta.get("provider", "")
        name = doc_id.split(":", 1)[1] if ":" in doc_id else doc_id

        score = r.get("score", 0)

        text = r.get("text", "")
        sentences = text.split(". ")
        snippet = sentences[1].rstrip(".") if len(sentences) > 1 else ""

        print(f"  {score:.3f}  {name} ({provider}){label_str}")
        if snippet:
            print(f"         {snippet}")
        print()
