from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

CATALOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "catalog"

SAMPLE_TEXT = (
    "Hi there, welcome back. I wanted to check in and see how you're doing today. "
    "Let me know if there's anything I can help with."
)


def _generate_rime(voice_id: str, model: str, out_dir: Path, client: httpx.Client) -> Path | None:
    api_key = os.environ.get("RIME_API_KEY", "")
    if not api_key:
        print("[enrich] RIME_API_KEY not set, skipping Rime samples")
        return None

    resp = client.post(
        "https://users.rime.ai/v1/rime-tts",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"text": SAMPLE_TEXT, "speaker": voice_id, "modelId": model},
    )
    resp.raise_for_status()
    path = out_dir / f"rime_{voice_id}.wav"
    path.write_bytes(resp.content)
    return path


def _generate_openai(voice_id: str, out_dir: Path, client: httpx.Client) -> Path | None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("[enrich] OPENAI_API_KEY not set, skipping OpenAI samples")
        return None

    resp = client.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": "tts-1", "voice": voice_id, "input": SAMPLE_TEXT},
    )
    resp.raise_for_status()
    path = out_dir / f"openai_{voice_id}.mp3"
    path.write_bytes(resp.content)
    return path


def _generate_elevenlabs(voice_id: str, out_dir: Path, client: httpx.Client) -> Path | None:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("[enrich] ELEVENLABS_API_KEY not set, skipping ElevenLabs samples")
        return None

    resp = client.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key},
        json={"text": SAMPLE_TEXT},
    )
    resp.raise_for_status()
    path = out_dir / f"elevenlabs_{voice_id}.mp3"
    path.write_bytes(resp.content)
    return path


def _generate_deepgram(voice_id: str, out_dir: Path, client: httpx.Client) -> Path | None:
    api_key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not api_key:
        print("[enrich] DEEPGRAM_API_KEY not set, skipping Deepgram samples")
        return None

    resp = client.post(
        f"https://api.deepgram.com/v1/speak?model={voice_id}",
        headers={"Authorization": f"Token {api_key}"},
        content=SAMPLE_TEXT,
    )
    resp.raise_for_status()
    path = out_dir / f"deepgram_{voice_id}.wav"
    path.write_bytes(resp.content)
    return path


_GENERATORS = {
    "rime": lambda v, d, c: _generate_rime(v["provider_voice_id"], v.get("provider_model", "mist"), d, c),
    "openai": lambda v, d, c: _generate_openai(v["provider_voice_id"], d, c),
    "elevenlabs": lambda v, d, c: _generate_elevenlabs(v["provider_voice_id"], d, c),
    "deepgram": lambda v, d, c: _generate_deepgram(v["provider_voice_id"], d, c),
}


def generate_sample(voice: dict, out_dir: Path, client: httpx.Client) -> Path | None:
    provider = voice["provider"]
    gen = _GENERATORS.get(provider)
    if gen is None:
        print(f"[enrich] No TTS generator for provider: {provider}")
        return None
    try:
        return gen(voice, out_dir, client)
    except httpx.HTTPStatusError as e:
        print(f"[enrich] HTTP {e.response.status_code} generating sample for {voice['id']}")
        return None
    except Exception as e:
        print(f"[enrich] Error generating sample for {voice['id']}: {e}")
        return None


def classify_voice(audio_path: Path, model: str = "qwen2-audio") -> dict | None:
    if model == "qwen2-audio":
        try:
            from voice_audition.enrich.classify import classify_audio
        except ImportError:
            print("[enrich] mlx-audio not installed. Install with: pip install 'voice-audition[enrich]'")
            return None
        return classify_audio(audio_path)

    print(f"[enrich] Unknown model: {model}")
    return None


def merge_enrichment(voice: dict, enrichment: dict) -> dict:
    voice = {**voice}
    for key in ("gender", "age_group", "accent", "description", "texture", "pitch"):
        if key in enrichment and enrichment[key]:
            voice[key] = enrichment[key]
    if "traits" in enrichment:
        existing = voice.get("traits") or {}
        merged = {**existing}
        for k, v in enrichment["traits"].items():
            if v is not None:
                merged[k] = v
        voice["traits"] = merged
    for key in ("personality_tags", "style_tags", "use_cases"):
        if key in enrichment and enrichment[key]:
            existing = set(voice.get(key, []))
            existing.update(enrichment[key])
            voice[key] = sorted(existing)
    if "enrichment" in enrichment:
        voice["enrichment"] = enrichment["enrichment"]
    voice["metadata_source"] = "enriched_local"
    voice["last_verified"] = datetime.now(timezone.utc).isoformat()
    return voice


def is_unenriched(voice: dict) -> bool:
    desc = voice.get("description", "") or ""
    if not desc or desc.startswith("Rime ") or len(desc) < 20:
        return True
    if voice.get("gender") == "unknown" and voice.get("metadata_source") == "provider_api":
        return True
    return False


def load_catalog(provider: str) -> list[dict] | None:
    path = CATALOG_DIR / f"{provider}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    return data.get("voices", [])


def save_catalog(provider: str, voices: list[dict]) -> None:
    path = CATALOG_DIR / f"{provider}.json"
    path.write_text(json.dumps(voices, indent=2, ensure_ascii=False))
    print(f"[enrich] Wrote {len(voices)} voices to {path}")


def run_enrich(providers: list[str] | None = None, model: str = "qwen2-audio"):
    """Run the enrichment pipeline."""
    skip = {"providers", "schema"}
    available = [p.stem for p in CATALOG_DIR.glob("*.json") if p.stem not in skip]
    targets = providers if providers else available
    targets = [p for p in targets if p in available]

    if not targets:
        print("[enrich] No catalog files found. Run sync first.")
        return

    total_voices = 0
    enriched_count = 0

    with tempfile.TemporaryDirectory(prefix="voice_enrich_") as tmp:
        out_dir = Path(tmp)

        with httpx.Client(timeout=30) as client:
            warned_providers: set[str] = set()

            for provider in targets:
                voices = load_catalog(provider)
                if voices is None:
                    print(f"[enrich] No catalog for {provider}, skipping")
                    continue

                unenriched = [v for v in voices if is_unenriched(v)]
                total_voices += len(unenriched)

                if not unenriched:
                    print(f"[enrich] {provider}: no unenriched voices")
                    continue

                print(f"[enrich] {provider}: {len(unenriched)} unenriched voices")

                updated = False
                for v in unenriched:
                    vid = v.get("id", v.get("provider_voice_id", "?"))
                    print(f"[enrich] Generating sample for {vid}...")

                    audio_path = generate_sample(v, out_dir, client)
                    if audio_path is None:
                        if provider not in warned_providers:
                            warned_providers.add(provider)
                        continue

                    print(f"[enrich] Classifying {vid}...")
                    result = classify_voice(audio_path, model=model)
                    if result is None:
                        continue

                    result["enrichment"] = {
                        "model": model,
                        "confidence": 0.7,
                        "sample_text": SAMPLE_TEXT,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    for i, entry in enumerate(voices):
                        if entry.get("id") == v.get("id"):
                            voices[i] = merge_enrichment(entry, result)
                            enriched_count += 1
                            updated = True
                            break

                if updated:
                    save_catalog(provider, voices)

    print(f"\n[enrich] Done. Enriched {enriched_count}/{total_voices} voices.")
