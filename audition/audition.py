from __future__ import annotations

import base64
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

from audition.db import add_audition_clip, create_audition_run, get_state_dir, update_audition_run
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
    "education": {
        "criteria": ["clarity", "patience", "encouragement", "structure", "warmth", "confidence"],
        "criteria_labels": {
            "clarity": "Clarity — easy to understand and follow?",
            "patience": "Patience — gives the listener room to think?",
            "encouragement": "Encouragement — supportive without sounding scripted?",
            "structure": "Structure — organizes information cleanly?",
            "warmth": "Warmth — friendly and welcoming?",
            "confidence": "Confidence — sounds informed and steady?",
        },
        "scripts": [
            {"name": "opening", "purpose": "Tests friendly instructional tone",
             "text": "Let's work through this together. There are no wrong answers here, and I'll guide you step by step."},
            {"name": "explanation", "purpose": "Tests clear teaching voice",
             "text": "First, we'll look at the main idea. Then we'll break it into smaller parts so it is easier to follow."},
            {"name": "encouragement", "purpose": "Tests supportive pacing",
             "text": "Take your time. If something is unclear, we can pause and come back to it whenever you're ready."},
            {"name": "wrap_up", "purpose": "Tests calm confidence",
             "text": "You have the basics now, and we'll keep building from here. You're doing well."},
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
    "education": ["education", "classroom", "lesson", "student", "teacher", "curriculum", "training", "school", "teach"],
}


def detect_use_case(brief: str) -> str:
    lower = brief.lower()
    scores = {k: sum(1 for w in words if w in lower) for k, words in _USE_CASE_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def get_profile(use_case: str) -> dict:
    return USE_CASE_PROFILES.get(use_case, DEFAULT_PROFILE)


def select_candidates(brief: str, num: int = 10, filters: dict | None = None) -> list[dict]:
    from audition.index import search_voices

    results = search_voices(brief, top_k=num * 2, filters=filters)["results"]
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


def _human_audition_scripts(use_case: str, brief: str) -> list[dict]:
    profile = get_profile(use_case)
    scripts = profile.get("scripts", [])[:2]
    if scripts:
        return [
            {
                "name": "business_context",
                "purpose": "Context-specific business phrase",
                "text": f"This voice will be used for: {brief}",
            },
            *scripts,
        ]
    return [
        {"name": "intro", "purpose": "Business-context introduction", "text": brief},
        {"name": "follow_up", "purpose": "Natural follow-up", "text": f"I'm calling about: {brief}"},
    ]


def run_human_audition(brief: str, num_candidates: int = 5,
                       gender: str | None = None, provider: str | None = None) -> dict:
    use_case = detect_use_case(brief)
    filters = {}
    if gender:
        filters["gender"] = gender
    if provider:
        filters["provider"] = provider

    candidates = select_candidates(brief, num=num_candidates, filters=filters)
    scripts = _human_audition_scripts(use_case, brief)
    storage_root = get_state_dir() / "clips"
    audition_run_id = create_audition_run("voice", "human", brief, use_case, "running")
    audition_dir = storage_root / f"audition-{audition_run_id}"
    audition_dir.mkdir(parents=True, exist_ok=True)

    clips = []
    with httpx.Client(timeout=30) as client:
        for voice in candidates:
            for script in scripts:
                path, error = _generate_script_audio(voice, script["text"], script["name"], audition_dir, client)
                clip = {
                    "audition_id": audition_run_id,
                    "voice_id": voice["id"],
                    "voice_name": voice.get("name"),
                    "provider": voice.get("provider"),
                    "script_name": script["name"],
                    "script_text": script["text"],
                    "file_path": str(path) if path else None,
                    "error": error,
                    "cost_per_min_usd": voice.get("effective_cost_per_min_usd"),
                }
                clips.append(clip)
                add_audition_clip(
                    audition_run_id,
                    voice["id"],
                    script["name"],
                    script["text"],
                    str(path) if path else None,
                    voice.get("provider"),
                    "completed" if path else "failed",
                    error=error,
                )

    result = {
        "mode": "human",
        "audition_id": audition_run_id,
        "use_case": use_case,
        "output_dir": str(audition_dir),
        "clips": clips,
    }
    update_audition_run(audition_run_id, status="completed", output_dir=str(audition_dir), result=result)
    return result


# ---------------------------------------------------------------------------
# Main audition — uses LangGraph audition graph
# ---------------------------------------------------------------------------

def run_audition(brief: str, num_candidates: int = 8, output_dir: str | None = None,
                 gender: str | None = None, provider: str | None = None,
                 mode: str = "ai"):
    if mode == "human":
        result = run_human_audition(brief, num_candidates=num_candidates, gender=gender, provider=provider)
        print(f"[audition] HUMAN AUDITION {result['audition_id']} stored in {result['output_dir']}")
        for clip in result["clips"]:
            status = "ok" if clip.get("file_path") else f"failed:{clip.get('error')}"
            print(
                f"  {clip['voice_name']} ({clip['provider']}) {clip['script_name']} "
                f"[{status}] cost={clip.get('cost_per_min_usd')}"
            )
            if clip.get("file_path"):
                print(f"    {clip['file_path']}")
        return result

    use_case = detect_use_case(brief)
    profile = get_profile(use_case)
    audition_run_id = create_audition_run("voice", "ai", brief, use_case, "running", output_dir=output_dir)
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
        print(
            f"  {c.get('name', '?')} ({c.get('provider')}) [{c.get('gender', '?')}] "
            f"score={c.get('search_score', 0):.3f} cost={c.get('effective_cost_per_min_usd')}"
        )
    print()

    from audition.graph import run_audition_graph

    profile_data = {
        "criteria": profile["criteria"],
        "criteria_labels": profile["criteria_labels"],
        "scripts": profile["scripts"],
    }

    result = run_audition_graph(brief, use_case, profile_data, candidates)
    scorecard = result.get("scorecard", [])

    # Save results
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="audition_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "scorecard.json").write_text(json.dumps({
        "brief": brief, "use_case": use_case,
        "profile": {"criteria": profile["criteria"], "criteria_labels": profile["criteria_labels"],
                     "scripts": [s["name"] for s in profile["scripts"]]},
        "scorecard": scorecard,
        "recommendation": scorecard[0] if scorecard else None,
        "candidate_notes": result.get("candidate_notes", []),
        "comparison_raw": result.get("comparison"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    print(f"\n{'=' * 50}")
    if scorecard and scorecard[0].get("total", 0) > 0:
        top = scorecard[0]
        print(f"[audition] RECOMMENDATION: {top.get('name')} ({top.get('provider')}) — {top['total']}/10")
        rec = top.get("recommendation")
        if rec:
            print(f"  {rec}")
        if top.get("strengths"):
            print(f"  Strengths: {top['strengths']}")
    print(f"[audition] Scorecard: {out_dir / 'scorecard.json'}")
    update_audition_run(
        audition_run_id,
        status="completed",
        output_dir=str(out_dir),
        result={"scorecard": scorecard, "output_dir": str(out_dir)},
    )
    return {"mode": "ai", "audition_id": audition_run_id, "scorecard": scorecard, "output_dir": str(out_dir)}
