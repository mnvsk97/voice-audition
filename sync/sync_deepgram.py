"""Sync voices from Deepgram Aura.

Deepgram has no voice listing API. Voices are documented statically.
This registry is maintained manually based on their documentation.
Voice ID format: aura-2-{name}-{lang}
"""

from common import normalize_voice, write_catalog

# Manually maintained from https://developers.deepgram.com/docs/tts-models
DEEPGRAM_VOICES = [
    # Aura-2 English voices
    {"name": "Thalia", "id": "aura-2-thalia-en", "gender": "female", "age": "middle", "accent": "american"},
    {"name": "Andromeda", "id": "aura-2-andromeda-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Arcas", "id": "aura-2-arcas-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Asteria", "id": "aura-2-asteria-en", "gender": "female", "age": "middle", "accent": "american"},
    {"name": "Athena", "id": "aura-2-athena-en", "gender": "female", "age": "middle", "accent": "british"},
    {"name": "Atlas", "id": "aura-2-atlas-en", "gender": "male", "age": "middle", "accent": "american"},
    {"name": "Helios", "id": "aura-2-helios-en", "gender": "male", "age": "middle", "accent": "british"},
    {"name": "Hera", "id": "aura-2-hera-en", "gender": "female", "age": "mature", "accent": "american"},
    {"name": "Luna", "id": "aura-2-luna-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Orion", "id": "aura-2-orion-en", "gender": "male", "age": "middle", "accent": "american"},
    {"name": "Perseus", "id": "aura-2-perseus-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Stella", "id": "aura-2-stella-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Zeus", "id": "aura-2-zeus-en", "gender": "male", "age": "mature", "accent": "american"},
    {"name": "Angus", "id": "aura-2-angus-en", "gender": "male", "age": "middle", "accent": "irish"},
    {"name": "Apollo", "id": "aura-2-apollo-en", "gender": "male", "age": "middle", "accent": "american"},
    {"name": "Cora", "id": "aura-2-cora-en", "gender": "female", "age": "middle", "accent": "american"},
    {"name": "Daphne", "id": "aura-2-daphne-en", "gender": "female", "age": "young", "accent": "british"},
    {"name": "Echo", "id": "aura-2-echo-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Electra", "id": "aura-2-electra-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Harmony", "id": "aura-2-harmony-en", "gender": "female", "age": "middle", "accent": "australian"},
    {"name": "Helena", "id": "aura-2-helena-en", "gender": "female", "age": "middle", "accent": "american"},
    {"name": "Hercules", "id": "aura-2-hercules-en", "gender": "male", "age": "mature", "accent": "american"},
    {"name": "Hermes", "id": "aura-2-hermes-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Iris", "id": "aura-2-iris-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Jason", "id": "aura-2-jason-en", "gender": "male", "age": "middle", "accent": "american"},
    {"name": "Juno", "id": "aura-2-juno-en", "gender": "female", "age": "middle", "accent": "american"},
    {"name": "Leda", "id": "aura-2-leda-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Lyra", "id": "aura-2-lyra-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Minerva", "id": "aura-2-minerva-en", "gender": "female", "age": "mature", "accent": "american"},
    {"name": "Neptune", "id": "aura-2-neptune-en", "gender": "male", "age": "mature", "accent": "british"},
    {"name": "Odysseus", "id": "aura-2-odysseus-en", "gender": "male", "age": "middle", "accent": "american"},
    {"name": "Ophelia", "id": "aura-2-ophelia-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Orpheus", "id": "aura-2-orpheus-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Pandora", "id": "aura-2-pandora-en", "gender": "female", "age": "middle", "accent": "american"},
    {"name": "Phoenix", "id": "aura-2-phoenix-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Poseidon", "id": "aura-2-poseidon-en", "gender": "male", "age": "mature", "accent": "american"},
    {"name": "Selene", "id": "aura-2-selene-en", "gender": "female", "age": "middle", "accent": "american"},
    {"name": "Titan", "id": "aura-2-titan-en", "gender": "male", "age": "middle", "accent": "american"},
    {"name": "Triton", "id": "aura-2-triton-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Vesta", "id": "aura-2-vesta-en", "gender": "female", "age": "middle", "accent": "american"},
    # Aura-1 legacy English voices
    {"name": "Asteria (v1)", "id": "aura-asteria-en", "gender": "female", "age": "middle", "accent": "american"},
    {"name": "Orion (v1)", "id": "aura-orion-en", "gender": "male", "age": "middle", "accent": "american"},
    {"name": "Luna (v1)", "id": "aura-luna-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Arcas (v1)", "id": "aura-arcas-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Stella (v1)", "id": "aura-stella-en", "gender": "female", "age": "young", "accent": "american"},
    {"name": "Athena (v1)", "id": "aura-athena-en", "gender": "female", "age": "middle", "accent": "british"},
    {"name": "Hera (v1)", "id": "aura-hera-en", "gender": "female", "age": "mature", "accent": "american"},
    {"name": "Perseus (v1)", "id": "aura-perseus-en", "gender": "male", "age": "young", "accent": "american"},
    {"name": "Angus (v1)", "id": "aura-angus-en", "gender": "male", "age": "middle", "accent": "irish"},
    {"name": "Helios (v1)", "id": "aura-helios-en", "gender": "male", "age": "middle", "accent": "british"},
    {"name": "Zeus (v1)", "id": "aura-zeus-en", "gender": "male", "age": "mature", "accent": "american"},
    {"name": "Atlas (v1)", "id": "aura-atlas-en", "gender": "male", "age": "middle", "accent": "american"},
]


def sync():
    voices = []

    for v in DEEPGRAM_VOICES:
        voices.append(normalize_voice(
            provider="deepgram",
            provider_voice_id=v["id"],
            name=v["name"],
            provider_model="aura-2" if v["id"].startswith("aura-2") else "aura-1",
            gender=v["gender"],
            age_group=v["age"],
            accent=v["accent"],
            language="en",
            provider_page_url="https://deepgram.com/product/text-to-speech",
            metadata_source="manual",
        ))

    write_catalog("deepgram", voices)


if __name__ == "__main__":
    sync()
