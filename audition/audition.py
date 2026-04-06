from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

from audition.index import semantic_search
from audition.search import load_all_voices

USE_CASE_PROFILES = {
    "healthcare": {
        "criteria": ["patient_comfort", "trust", "empathy", "clarity", "pacing", "sensitivity"],
        "criteria_labels": {
            "patient_comfort": "Patient Comfort — would anxious patients feel at ease?",
            "trust": "Trust — does this sound experienced and reliable?",
            "empathy": "Empathy — does the voice convey genuine care?",
            "clarity": "Clarity — can a stressed person easily understand?",
            "pacing": "Pacing — appropriate speed for sensitive conversations?",
            "sensitivity": "Sensitivity — handles difficult moments with grace?",
        },
        "scripts": [
            {"name": "greeting", "purpose": "Tests warmth and professionalism on first contact",
             "text": "Hi there, thank you for calling. How are you doing today? I'm here to help with whatever you need."},
            {"name": "empathy", "purpose": "Tests sincerity during emotional moment",
             "text": "I completely understand how stressful this process can be. You're not alone in feeling this way, and we're here to support you every step."},
            {"name": "information", "purpose": "Tests clarity when delivering details",
             "text": "Your next appointment is scheduled for Thursday at 2 PM with Dr. Chen. I'll send you the preparation instructions by email. Is there anything else you'd like to know?"},
            {"name": "difficult_moment", "purpose": "Tests sensitivity with hard conversations",
             "text": "I see that the doctor would like to discuss some results with you. Let me connect you with the care team right away. Please know that we're here for you."},
        ],
    },
    "sales": {
        "criteria": ["energy", "rapport", "persuasiveness", "confidence", "resilience", "likability"],
        "criteria_labels": {
            "energy": "Energy — engaging without being pushy?",
            "rapport": "Rapport — builds connection quickly?",
            "persuasiveness": "Persuasiveness — naturally convincing?",
            "confidence": "Confidence — sounds assured and knowledgeable?",
            "resilience": "Resilience — handles objections gracefully?",
            "likability": "Likability — would you keep talking to this voice?",
        },
        "scripts": [
            {"name": "cold_open", "purpose": "Tests energy and rapport in first 10 seconds",
             "text": "Hey, this is Alex calling from Bright Solutions. I know you're busy, so I'll be quick — I noticed you were looking into upgrading your team's workflow, and I have something that might be exactly what you need."},
            {"name": "value_pitch", "purpose": "Tests persuasiveness and clarity",
             "text": "What we've seen with similar companies is a 40 percent reduction in manual work within the first month. And the best part? Your team can start using it today with zero setup required."},
            {"name": "objection_handling", "purpose": "Tests resilience and confidence under pushback",
             "text": "I totally hear you — budget is tight right now for everyone. That's exactly why I'm calling, because this actually saves money from day one. Can I show you the numbers? It'll take two minutes."},
            {"name": "close", "purpose": "Tests confident closing without pressure",
             "text": "Great, I'll send over a personalized demo link right now. If it's not a fit, no worries at all — but I think you'll be pleasantly surprised. Talk soon!"},
        ],
    },
    "customer_support": {
        "criteria": ["patience", "clarity", "helpfulness", "professionalism", "warmth", "resolution_focus"],
        "criteria_labels": {
            "patience": "Patience — stays calm with frustrated callers?",
            "clarity": "Clarity — explains things simply?",
            "helpfulness": "Helpfulness — sounds genuinely eager to solve?",
            "professionalism": "Professionalism — maintains composure?",
            "warmth": "Warmth — friendly without being fake?",
            "resolution_focus": "Resolution Focus — drives toward solution?",
        },
        "scripts": [
            {"name": "greeting", "purpose": "Tests professionalism and warmth",
             "text": "Thank you for calling support, my name is Alex. I can see your account here. How can I help you today?"},
            {"name": "troubleshooting", "purpose": "Tests clarity and patience",
             "text": "Okay, let's try this together. First, can you go to your settings menu? It should be the gear icon in the top right corner. Let me know when you see it."},
            {"name": "angry_caller", "purpose": "Tests composure under pressure",
             "text": "I completely understand your frustration, and I'm sorry you've had this experience. Let me take care of this for you right now. I'm going to make sure this gets resolved today."},
            {"name": "escalation", "purpose": "Tests graceful handoff",
             "text": "I want to make sure you get the best help possible, so I'm going to connect you with our specialist team. I've noted everything we discussed so you won't need to repeat yourself."},
        ],
    },
    "finance": {
        "criteria": ["authority", "precision", "trustworthiness", "calm", "professionalism", "compliance_tone"],
        "criteria_labels": {
            "authority": "Authority — sounds knowledgeable and credible?",
            "precision": "Precision — delivers numbers and details clearly?",
            "trustworthiness": "Trustworthiness — would you trust this voice with your money?",
            "calm": "Calm — steady even with large numbers?",
            "professionalism": "Professionalism — appropriate gravitas?",
            "compliance_tone": "Compliance Tone — sounds like official communication?",
        },
        "scripts": [
            {"name": "greeting", "purpose": "Tests professional authority",
             "text": "Good afternoon, thank you for calling. I have your account pulled up. How may I assist you today?"},
            {"name": "numbers", "purpose": "Tests precision with financial data",
             "text": "Your current balance is twelve thousand four hundred and thirty-seven dollars and fifty-two cents. The last transaction was a payment of two hundred and fifteen dollars on March twenty-eighth."},
            {"name": "security", "purpose": "Tests trustworthiness in sensitive context",
             "text": "For your security, I need to verify your identity. Can you please confirm the last four digits of your social security number and your date of birth?"},
            {"name": "advisory", "purpose": "Tests authoritative guidance",
             "text": "Based on your current portfolio, I'd recommend reviewing your allocation. Market conditions have shifted, and there may be an opportunity to optimize your returns while managing risk."},
        ],
    },
    "meditation": {
        "criteria": ["calm", "spaciousness", "grounding", "non_intrusive", "breath_quality", "presence"],
        "criteria_labels": {
            "calm": "Calm — genuinely peaceful, not performative?",
            "spaciousness": "Spaciousness — leaves room for stillness?",
            "grounding": "Grounding — anchors the listener?",
            "non_intrusive": "Non-Intrusive — guides without commanding?",
            "breath_quality": "Breath Quality — natural breathing pattern?",
            "presence": "Presence — feels like someone is truly there?",
        },
        "scripts": [
            {"name": "opening", "purpose": "Tests calm presence",
             "text": "Welcome. Find a comfortable position and gently close your eyes. Take a deep breath in... and slowly release."},
            {"name": "body_scan", "purpose": "Tests spaciousness and pacing",
             "text": "Now bring your attention to your feet. Notice any sensations there. There's no need to change anything. Just observe. Slowly move your awareness up through your ankles... your calves... your knees."},
            {"name": "difficult_emotion", "purpose": "Tests gentleness with vulnerability",
             "text": "If any difficult thoughts or feelings arise, that's perfectly okay. Simply acknowledge them, like clouds passing through the sky. You don't need to hold on. Let them drift."},
            {"name": "closing", "purpose": "Tests warm grounding",
             "text": "When you're ready, gently bring your awareness back to the room. Wiggle your fingers and toes. Take one more deep breath. Welcome back."},
        ],
    },
}

DEFAULT_PROFILE = {
    "criteria": ["warmth", "clarity", "professionalism", "energy", "trustworthiness", "fit"],
    "criteria_labels": {
        "warmth": "Warmth — approachable and caring?",
        "clarity": "Clarity — easy to understand?",
        "professionalism": "Professionalism — appropriate tone?",
        "energy": "Energy — right level of engagement?",
        "trustworthiness": "Trustworthiness — credible and reliable?",
        "fit": "Overall Fit — right for this specific use case?",
    },
    "scripts": [
        {"name": "greeting", "purpose": "Tests first impression",
         "text": "Hi there, welcome. I'm here to help you today. What can I do for you?"},
        {"name": "explanation", "purpose": "Tests clarity and engagement",
         "text": "Let me walk you through how this works. It's actually quite simple — there are just three steps, and I'll guide you through each one."},
        {"name": "empathy", "purpose": "Tests emotional handling",
         "text": "I understand that can be frustrating. Let's see what we can do to make this right for you."},
    ],
}

_USE_CASE_KEYWORDS = {
    "healthcare": ["healthcare", "medical", "patient", "clinic", "hospital", "doctor", "therapy", "fertility", "dental", "pharmacy", "wellness"],
    "sales": ["sales", "cold call", "outbound", "lead", "conversion", "pitch", "prospect", "real estate"],
    "customer_support": ["support", "customer service", "help desk", "call center", "complaint", "troubleshoot"],
    "finance": ["finance", "financial", "banking", "investment", "insurance", "loan", "mortgage", "credit", "wealth"],
    "meditation": ["meditation", "mindfulness", "yoga", "sleep", "relaxation", "calm", "breathing"],
}


def detect_use_case(brief: str) -> str:
    lower = brief.lower()
    scores = {k: sum(1 for w in words if w in lower) for k, words in _USE_CASE_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def get_profile(use_case: str) -> dict:
    return USE_CASE_PROFILES.get(use_case, DEFAULT_PROFILE)


def select_candidates(brief: str, num: int = 10, filters: dict | None = None) -> list[dict]:
    results = asyncio.run(semantic_search(brief, top_k=num * 2, filters=filters))
    all_voices = {v["id"]: v for v in load_all_voices()}
    candidates = []
    for r in results:
        voice = all_voices.get(r["id"])
        if voice:
            voice["search_score"] = r["score"]
            candidates.append(voice)
        if len(candidates) >= num:
            break
    return candidates


# ---------------------------------------------------------------------------
# Audio generation for audition scripts
# ---------------------------------------------------------------------------

def _generate_script_audio(voice: dict, text: str, script_name: str, out_dir: Path, client: httpx.Client) -> tuple[Path | None, str | None]:
    """Generate audio for a specific script text using the voice's TTS provider."""
    provider = voice.get("provider")
    voice_id = voice.get("provider_voice_id", "")
    model = voice.get("provider_model", "")

    try:
        if provider == "rime":
            api_key = os.environ.get("RIME_API_KEY", "")
            if not api_key: return None, "no_api_key"
            speaker = voice_id.split(":")[-1]
            body = {"text": text, "speaker": speaker, "modelId": model}
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            if model in ("arcana", "mistv3"):
                headers["Accept"] = "audio/wav"
            resp = client.post("https://users.rime.ai/v1/rime-tts", headers=headers, json=body)
            resp.raise_for_status()
            audio = resp.content if model in ("arcana", "mistv3") else base64.b64decode(resp.json()["audioContent"])
        elif provider == "elevenlabs":
            api_key = os.environ.get("ELEVENLABS_API_KEY", "")
            if not api_key: return None, "no_api_key"
            resp = client.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                               headers={"xi-api-key": api_key}, json={"text": text})
            resp.raise_for_status()
            audio = resp.content
        elif provider == "deepgram":
            api_key = os.environ.get("DEEPGRAM_API_KEY", "")
            if not api_key: return None, "no_api_key"
            resp = client.post(f"https://api.deepgram.com/v1/speak?model={voice_id}",
                               headers={"Authorization": f"Token {api_key}"}, content=text)
            resp.raise_for_status()
            audio = resp.content
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key: return None, "no_api_key"
            resp = client.post("https://api.openai.com/v1/audio/speech",
                               headers={"Authorization": f"Bearer {api_key}"},
                               json={"model": model or "gpt-4o-mini-tts", "voice": voice_id, "input": text})
            resp.raise_for_status()
            audio = resp.content
        else:
            return None, f"unsupported_provider:{provider}"

        ext = ".wav" if provider == "rime" else ".mp3"
        path = out_dir / f"{voice['id'].replace(':', '_')}_{script_name}{ext}"
        path.write_bytes(audio)
        return path, None
    except httpx.HTTPStatusError as e:
        return None, f"http_{e.response.status_code}"
    except Exception as e:
        return None, str(e)[:80]


# ---------------------------------------------------------------------------
# LLM judging — uses enrichment config (any provider)
# ---------------------------------------------------------------------------

def _build_judge_prompt(brief: str, use_case: str, criteria_labels: dict, script: dict) -> str:
    criteria_str = "\n".join(f"- {k}: {v}" for k, v in criteria_labels.items())
    return f"""You are judging a voice for: "{brief}" (category: {use_case}).

Audio is the voice reading: "{script['text']}"
Script purpose: {script['purpose']}

Score each criterion 1-10. Be harsh — differentiate clearly.

CRITERIA:
{criteria_str}

Respond with ONLY JSON:
{{"scores": {{{", ".join(f'"{k}": 0' for k in criteria_labels)}}}, "notes": "1-2 sentences on fit"}}"""


def _judge_audio(audio_path: Path, prompt: str, judge_provider: str, judge_config: dict) -> dict | None:
    """Score a voice sample using the configured enrichment provider."""
    from enrichment.classify import _read_audio_b64

    b64, fmt = _read_audio_b64(audio_path)
    mime = {"wav": "audio/wav", "mp3": "audio/mpeg"}.get(fmt, "audio/wav")

    try:
        if judge_provider == "gemini":
            raw = _judge_gemini(b64, mime, prompt, judge_config)
        elif judge_provider == "openai":
            raw = _judge_openai(b64, fmt, prompt, judge_config)
        elif judge_provider == "ollama":
            raw = _judge_ollama(b64, prompt, judge_config)
        elif judge_provider == "mlx":
            raw = _judge_mlx(audio_path, prompt, judge_config)
        elif judge_provider in ("anthropic", "bedrock"):
            # Text-only models can't listen to audio — score from voice metadata instead
            return None
        else:
            return None
    except Exception as e:
        print(f"  [judge] Error: {e}")
        return None

    if not raw:
        return None
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def _judge_gemini(b64: str, mime: str, prompt: str, config: dict) -> str | None:
    model = config.get("model", "gemini-2.0-flash")
    creds = config.get("credentials_file")
    if creds:
        from enrichment.classify import _get_gemini_token_from_sa
        token = _get_gemini_token_from_sa(str(Path(creds).expanduser()))
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={config['api_key']}"
        headers = {"Content-Type": "application/json"}

    resp = httpx.post(url, headers=headers, json={
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": b64}}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 256},
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _judge_openai(b64: str, fmt: str, prompt: str, config: dict) -> str | None:
    base_url = config.get("base_url", "https://api.openai.com/v1").rstrip("/")
    resp = httpx.post(f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {config['api_key']}"},
        json={
            "model": config.get("model", "gpt-4o"),
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "input_audio", "input_audio": {"data": b64, "format": fmt}},
            ]}],
            "max_tokens": 256, "temperature": 0.1,
        }, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _judge_ollama(b64: str, prompt: str, config: dict) -> str | None:
    base_url = config.get("base_url", "http://localhost:11434").rstrip("/")
    resp = httpx.post(f"{base_url}/api/chat", json={
        "model": config.get("model", "qwen2-audio"),
        "messages": [{"role": "user", "content": prompt, "images": [b64]}],
        "stream": False, "options": {"temperature": 0.1},
    }, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def _judge_mlx(audio_path: Path, prompt: str, config: dict) -> str | None:
    from enrichment.classify import enrich_mlx
    # Reuse MLX model loading, but with our judge prompt
    global _mlx_model, _mlx_model_name
    model_id = config.get("model_id", "mlx-community/Qwen2-Audio-7B-Instruct-4bit")
    from enrichment.classify import _mlx_model, _mlx_model_name as _mn
    if _mlx_model is None or _mn != model_id:
        from mlx_audio.stt.utils import load_model
        import enrichment.classify as cl
        cl._mlx_model = load_model(model_id)
        cl._mlx_model_name = model_id
    result = _mlx_model.generate(str(audio_path), prompt=prompt, max_tokens=256, temperature=0.1)
    return result.text.strip()


# ---------------------------------------------------------------------------
# Main audition
# ---------------------------------------------------------------------------

def _load_judge_config() -> tuple[str, dict] | None:
    """Load enrichment config for judging. Returns (provider, config) or None."""
    try:
        from enrichment.config import load_config, get_provider_config, validate_credentials
        config = load_config()
        provider, provider_config = get_provider_config(config)
        validate_credentials(provider, provider_config)
        return provider, provider_config
    except Exception as e:
        print(f"[audition] No judge LLM configured: {e}")
        return None


def run_audition(brief: str, num_candidates: int = 8, output_dir: str | None = None,
                 gender: str | None = None, provider: str | None = None):
    use_case = detect_use_case(brief)
    profile = get_profile(use_case)
    print(f"[audition] Use case: {use_case} | Criteria: {', '.join(profile['criteria'])} | Scripts: {len(profile['scripts'])}\n")

    filters = {}
    if gender:
        filters["gender"] = gender
    if provider:
        filters["provider"] = provider

    candidates = select_candidates(brief, num=num_candidates, filters=filters)
    if not candidates:
        print("[audition] No candidates found.")
        return

    print(f"[audition] {len(candidates)} candidates")
    for c in candidates:
        print(f"  {c.get('name', '?')} ({c.get('provider')}) [{c.get('gender', '?')}] score={c.get('search_score', 0):.3f}")
    print()

    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="audition_"))
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    # Phase 1: Generate audio
    print("[audition] Generating audio samples...")
    candidate_audio: dict[str, list[dict]] = {}
    with httpx.Client(timeout=30) as client:
        for c in candidates:
            results = []
            for script in profile["scripts"]:
                path, err = _generate_script_audio(c, script["text"], script["name"], audio_dir, client)
                results.append({"name": script["name"], "path": str(path) if path else None, "error": err})
            candidate_audio[c["id"]] = results
            ok = sum(1 for a in results if a["path"])
            print(f"  {c.get('name', '?')}: {ok}/{len(results)} scripts" +
                  (f" ({len(results) - ok} failed)" if ok < len(results) else ""))

    # Phase 2: LLM judges
    judge = _load_judge_config()
    scorecard: list[dict] = []

    if judge:
        judge_provider, judge_config = judge
        print(f"\n[audition] Judging with {judge_provider}...")
        for c in candidates:
            voice_scores: dict[str, list[int]] = {k: [] for k in profile["criteria"]}
            voice_notes = []
            for i, script in enumerate(profile["scripts"]):
                audio_info = candidate_audio[c["id"]][i]
                if not audio_info["path"]:
                    continue
                prompt = _build_judge_prompt(brief, use_case, profile["criteria_labels"], script)
                result = _judge_audio(Path(audio_info["path"]), prompt, judge_provider, judge_config)
                if result and "scores" in result:
                    for k in profile["criteria"]:
                        s = result["scores"].get(k)
                        if isinstance(s, (int, float)) and 1 <= s <= 10:
                            voice_scores[k].append(int(s))
                    if result.get("notes"):
                        voice_notes.append(result["notes"])

            avg = {k: round(sum(v) / len(v), 1) if v else 0 for k, v in voice_scores.items()}
            total = round(sum(avg.values()) / len(avg), 1) if avg else 0
            scorecard.append({
                "id": c["id"], "name": c.get("name"), "provider": c.get("provider"),
                "gender": c.get("gender"), "search_score": c.get("search_score", 0),
                "scores": avg, "total": total, "notes": voice_notes,
                "audio_files": [a["path"] for a in candidate_audio[c["id"]] if a["path"]],
            })
            print(f"  {c.get('name', '?')}: {total}/10")

        scorecard.sort(key=lambda x: x["total"], reverse=True)
    else:
        print("\n[audition] No judge configured — audio files saved for manual review.")
        for c in candidates:
            scorecard.append({
                "id": c["id"], "name": c.get("name"), "provider": c.get("provider"),
                "gender": c.get("gender"), "search_score": c.get("search_score", 0),
                "scores": {}, "total": 0, "notes": [],
                "audio_files": [a["path"] for a in candidate_audio[c["id"]] if a["path"]],
            })

    # Save results
    (out_dir / "scorecard.json").write_text(json.dumps({
        "brief": brief, "use_case": use_case,
        "judge": {"provider": judge[0], "model": judge[1].get("model", judge[1].get("model_id", "default"))} if judge else None,
        "profile": {"criteria": profile["criteria"], "criteria_labels": profile["criteria_labels"],
                     "scripts": [s["name"] for s in profile["scripts"]]},
        "scorecard": scorecard,
        "recommendation": scorecard[0] if scorecard else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    print(f"\n{'=' * 50}")
    if scorecard and scorecard[0]["total"] > 0:
        top = scorecard[0]
        print(f"[audition] RECOMMENDATION: {top['name']} ({top['provider']}) — {top['total']}/10")
        if top["notes"]:
            print(f"  {top['notes'][0]}")
    print(f"[audition] Scorecard: {out_dir / 'scorecard.json'}")
    print(f"[audition] Audio: {audio_dir}")
