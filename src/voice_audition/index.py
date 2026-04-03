"""Moss semantic search index for the voice catalog.

Builds a Moss vector index from catalog voices and provides
hybrid (semantic + keyword) search over it.
"""

import asyncio
import os

from moss import DocumentInfo, MossClient, QueryOptions

from voice_audition.search import load_all_voices


def _trait_label(value: float) -> str:
    """Translate a 0-1 trait score to a word."""
    if value < 0.3:
        return "low"
    elif value <= 0.7:
        return "moderate"
    else:
        return "high"


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

    # --- Build text for semantic search ---
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

    if description:
        parts.append(description)

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

    # --- Build metadata (all string values) ---
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

    # Deduplicate by ID (keep first occurrence)
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
    """Sync wrapper for build_index(). For CLI use."""
    asyncio.run(build_index(force=force))


def run_semantic_search(query: str, top_k: int = 5) -> None:
    """Sync wrapper that runs semantic_search() and prints results."""
    results = asyncio.run(semantic_search(query, top_k=top_k))
    time_ms = "?"
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

        # Extract name and provider from id (format: "provider:voice_id")
        doc_id = r.get("id", "")
        provider = meta.get("provider", "")
        name = doc_id.split(":", 1)[1] if ":" in doc_id else doc_id

        score = r.get("score", 0)

        # First line of text as description snippet
        text = r.get("text", "")
        # Grab the second sentence as a brief description
        sentences = text.split(". ")
        snippet = sentences[1].rstrip(".") if len(sentences) > 1 else ""

        print(f"  {score:.3f}  {name} ({provider}){label_str}")
        if snippet:
            print(f"         {snippet}")
        print()
