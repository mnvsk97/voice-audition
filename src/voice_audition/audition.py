from __future__ import annotations

import asyncio
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

from voice_audition.index import semantic_search
from voice_audition.search import load_all_voices

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
            {
                "name": "greeting",
                "purpose": "Tests warmth and professionalism on first contact",
                "text": "Hi there, thank you for calling. How are you doing today? I'm here to help with whatever you need.",
            },
            {
                "name": "empathy",
                "purpose": "Tests sincerity during emotional moment",
                "text": "I completely understand how stressful this process can be. You're not alone in feeling this way, and we're here to support you every step.",
            },
            {
                "name": "information",
                "purpose": "Tests clarity when delivering details",
                "text": "Your next appointment is scheduled for Thursday at 2 PM with Dr. Chen. I'll send you the preparation instructions by email. Is there anything else you'd like to know?",
            },
            {
                "name": "difficult_moment",
                "purpose": "Tests sensitivity with hard conversations",
                "text": "I see that the doctor would like to discuss some results with you. Let me connect you with the care team right away. Please know that we're here for you.",
            },
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
            {
                "name": "cold_open",
                "purpose": "Tests energy and rapport in first 10 seconds",
                "text": "Hey, this is Alex calling from Bright Solutions. I know you're busy, so I'll be quick — I noticed you were looking into upgrading your team's workflow, and I have something that might be exactly what you need.",
            },
            {
                "name": "value_pitch",
                "purpose": "Tests persuasiveness and clarity",
                "text": "What we've seen with similar companies is a 40 percent reduction in manual work within the first month. And the best part? Your team can start using it today with zero setup required.",
            },
            {
                "name": "objection_handling",
                "purpose": "Tests resilience and confidence under pushback",
                "text": "I totally hear you — budget is tight right now for everyone. That's exactly why I'm calling, because this actually saves money from day one. Can I show you the numbers? It'll take two minutes.",
            },
            {
                "name": "close",
                "purpose": "Tests confident closing without pressure",
                "text": "Great, I'll send over a personalized demo link right now. If it's not a fit, no worries at all — but I think you'll be pleasantly surprised. Talk soon!",
            },
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
            {
                "name": "greeting",
                "purpose": "Tests professionalism and warmth",
                "text": "Thank you for calling support, my name is Alex. I can see your account here. How can I help you today?",
            },
            {
                "name": "troubleshooting",
                "purpose": "Tests clarity and patience",
                "text": "Okay, let's try this together. First, can you go to your settings menu? It should be the gear icon in the top right corner. Let me know when you see it.",
            },
            {
                "name": "angry_caller",
                "purpose": "Tests composure under pressure",
                "text": "I completely understand your frustration, and I'm sorry you've had this experience. Let me take care of this for you right now. I'm going to make sure this gets resolved today.",
            },
            {
                "name": "escalation",
                "purpose": "Tests graceful handoff",
                "text": "I want to make sure you get the best help possible, so I'm going to connect you with our specialist team. I've noted everything we discussed so you won't need to repeat yourself.",
            },
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
            {
                "name": "greeting",
                "purpose": "Tests professional authority",
                "text": "Good afternoon, thank you for calling. I have your account pulled up. How may I assist you today?",
            },
            {
                "name": "numbers",
                "purpose": "Tests precision with financial data",
                "text": "Your current balance is twelve thousand four hundred and thirty-seven dollars and fifty-two cents. The last transaction was a payment of two hundred and fifteen dollars on March twenty-eighth.",
            },
            {
                "name": "security",
                "purpose": "Tests trustworthiness in sensitive context",
                "text": "For your security, I need to verify your identity. Can you please confirm the last four digits of your social security number and your date of birth?",
            },
            {
                "name": "advisory",
                "purpose": "Tests authoritative guidance",
                "text": "Based on your current portfolio, I'd recommend reviewing your allocation. Market conditions have shifted, and there may be an opportunity to optimize your returns while managing risk.",
            },
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
            {
                "name": "opening",
                "purpose": "Tests calm presence",
                "text": "Welcome. Find a comfortable position and gently close your eyes. Take a deep breath in... and slowly release.",
            },
            {
                "name": "body_scan",
                "purpose": "Tests spaciousness and pacing",
                "text": "Now bring your attention to your feet. Notice any sensations there. There's no need to change anything. Just observe. Slowly move your awareness up through your ankles... your calves... your knees.",
            },
            {
                "name": "difficult_emotion",
                "purpose": "Tests gentleness with vulnerability",
                "text": "If any difficult thoughts or feelings arise, that's perfectly okay. Simply acknowledge them, like clouds passing through the sky. You don't need to hold on. Let them drift.",
            },
            {
                "name": "closing",
                "purpose": "Tests warm grounding",
                "text": "When you're ready, gently bring your awareness back to the room. Wiggle your fingers and toes. Take one more deep breath. Welcome back.",
            },
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
        {
            "name": "greeting",
            "purpose": "Tests first impression",
            "text": "Hi there, welcome. I'm here to help you today. What can I do for you?",
        },
        {
            "name": "explanation",
            "purpose": "Tests clarity and engagement",
            "text": "Let me walk you through how this works. It's actually quite simple — there are just three steps, and I'll guide you through each one.",
        },
        {
            "name": "empathy",
            "purpose": "Tests emotional handling",
            "text": "I understand that can be frustrating. Let's see what we can do to make this right for you.",
        },
    ],
}


def detect_use_case(brief: str) -> str:
    lower = brief.lower()
    keywords = {
        "healthcare": ["healthcare", "medical", "patient", "clinic", "hospital", "doctor", "nurse", "therapy", "fertility", "dental", "pharmacy", "wellness"],
        "sales": ["sales", "cold call", "outbound", "lead", "conversion", "pitch", "prospect", "real estate", "insurance"],
        "customer_support": ["support", "customer service", "help desk", "call center", "contact center", "complaint", "troubleshoot"],
        "finance": ["finance", "financial", "banking", "bank", "investment", "insurance", "loan", "mortgage", "credit", "accounting", "tax", "wealth", "portfolio"],
        "meditation": ["meditation", "mindfulness", "yoga", "sleep", "relaxation", "calm", "breathing", "wellness app"],
    }
    scores = {}
    for category, words in keywords.items():
        scores[category] = sum(1 for w in words if w in lower)
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


JUDGE_PROMPT_TEMPLATE = """You are a professional voice casting director judging a voice for the following role:

ROLE: {brief}
USE CASE: {use_case}

You are evaluating this voice reading the following script:
SCRIPT: "{script_text}"
PURPOSE: {script_purpose}

Listen carefully to the audio. Score this voice on each criterion below from 0 to 10:
{criteria_text}

Also provide:
- A one-sentence assessment of how well this voice fits the role
- Any concerns or red flags

Respond ONLY with JSON:
{{
  "scores": {{"criterion_name": score, ...}},
  "assessment": "one sentence",
  "concerns": "any concerns or empty string"
}}"""


def build_judge_prompt(brief: str, use_case: str, script: dict, profile: dict) -> str:
    criteria_text = "\n".join(
        f"- {name}: {label} (0=terrible, 5=adequate, 10=perfect)"
        for name, label in profile["criteria_labels"].items()
    )
    return JUDGE_PROMPT_TEMPLATE.format(
        brief=brief,
        use_case=use_case,
        script_text=script["text"],
        script_purpose=script["purpose"],
        criteria_text=criteria_text,
    )


def generate_audio(voice: dict, text: str, out_path: Path, client: httpx.Client) -> bool:
    provider = voice.get("provider")
    voice_id = voice.get("provider_voice_id", "")

    try:
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                return False
            resp = client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "tts-1", "voice": voice_id, "input": text},
            )
        elif provider == "elevenlabs":
            api_key = os.environ.get("ELEVENLABS_API_KEY", "")
            if not api_key:
                return False
            resp = client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={"xi-api-key": api_key},
                json={"text": text},
            )
        elif provider == "deepgram":
            api_key = os.environ.get("DEEPGRAM_API_KEY", "")
            if not api_key:
                return False
            resp = client.post(
                f"https://api.deepgram.com/v1/speak?model={voice_id}",
                headers={"Authorization": f"Token {api_key}"},
                content=text,
            )
        elif provider == "rime":
            api_key = os.environ.get("RIME_API_KEY", "")
            if not api_key:
                return False
            model = voice.get("provider_model", "mist")
            name = voice_id.split(":")[-1] if ":" in voice_id else voice_id
            resp = client.post(
                "https://users.rime.ai/v1/rime-tts",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"text": text, "speaker": name, "modelId": model},
            )
        else:
            return False

        resp.raise_for_status()
        out_path.write_bytes(resp.content)
        return True

    except Exception as e:
        print(f"  [audio] Error for {voice.get('id')}: {e}")
        return False


def judge_voice(audio_path: Path, prompt: str) -> dict | None:
    try:
        from voice_audition.enrich.classify import _load_model
    except ImportError:
        print("[audition] mlx-audio not installed.")
        return None

    model = _load_model()
    result = model.generate(str(audio_path), prompt=prompt, max_tokens=300, temperature=0.1)
    raw = result.text.strip()

    # Parse JSON from response
    import re
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not json_match:
        return None
    try:
        return json.loads(json_match.group())
    except json.JSONDecodeError:
        return None


def format_scorecard(brief: str, use_case: str, profile: dict, results: list[dict], out_dir: Path | None = None) -> str:
    lines = []
    lines.append(f"AUDITION: {brief}")
    lines.append(f"Use case: {use_case}")
    lines.append(f"Candidates: {len(results)}")
    lines.append("")

    # Sort by total score descending
    for r in results:
        r["total"] = sum(r.get("scene_totals", {}).values())
    results.sort(key=lambda r: -r["total"])

    max_score = len(profile["scripts"]) * len(profile["criteria"]) * 10

    # Header
    criteria_short = [c[:8] for c in profile["criteria"]]
    header = f"  {'Voice':<25} {'Provider':<12} " + " ".join(f"{c:>8}" for c in criteria_short) + f" {'TOTAL':>8}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))

    for r in results:
        name = r.get("name", "?")[:24]
        provider = r.get("provider", "?")[:11]
        avgs = r.get("criteria_averages", {})
        avg_strs = [f"{avgs.get(c, 0):>8.1f}" for c in profile["criteria"]]
        total = r["total"]
        lines.append(f"  {name:<25} {provider:<12} " + " ".join(avg_strs) + f" {total:>7}/{max_score}")

        if r.get("assessment"):
            lines.append(f"  {'':>25} {r['assessment']}")
        if r.get("concerns"):
            lines.append(f"  {'':>25} CONCERN: {r['concerns']}")
        lines.append("")

    if results:
        winner = results[0]
        lines.append(f"RECOMMENDATION: {winner.get('name')} ({winner.get('provider')})")
        if winner.get("assessment"):
            lines.append(f"  {winner['assessment']}")

    if out_dir:
        lines.append(f"\nAudio samples saved to: {out_dir}")

    return "\n".join(lines)


def run_audition(
    brief: str,
    num_candidates: int = 8,
    output_dir: str | None = None,
    gender: str | None = None,
    provider: str | None = None,
):
    # Analyze brief
    use_case = detect_use_case(brief)
    profile = get_profile(use_case)
    print(f"[audition] Use case detected: {use_case}")
    print(f"[audition] Criteria: {', '.join(profile['criteria'])}")
    print(f"[audition] Test scripts: {len(profile['scripts'])}")
    print()

    filters = {}
    if gender:
        filters["gender"] = gender
    if provider:
        filters["provider"] = provider

    print(f"[audition] Searching for candidates...")
    candidates = select_candidates(brief, num=num_candidates, filters=filters)
    print(f"[audition] Found {len(candidates)} candidates")
    for c in candidates:
        print(f"  {c.get('name', '?')} ({c.get('provider')}) [{c.get('gender', '?')}] score={c.get('search_score', 0):.3f}")
    print()

    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="audition_"))
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    results = []

    with httpx.Client(timeout=30) as client:
        for candidate in candidates:
            cid = candidate.get("id", "?")
            cname = candidate.get("name", "?")
            print(f"[audition] Auditioning: {cname} ({candidate.get('provider')})")

            scene_scores = {}
            scene_totals = {}
            all_scores = {}
            assessment = ""
            concerns = ""

            has_audio = False

            for script in profile["scripts"]:
                sname = script["name"]
                audio_path = audio_dir / f"{cid.replace(':', '_')}_{sname}.wav"

                ok = generate_audio(candidate, script["text"], audio_path, client)
                if not ok:
                    print(f"  [skip] No API key for {candidate.get('provider')}")
                    break

                has_audio = True
                print(f"  [scene] {sname}: generated")

                prompt = build_judge_prompt(brief, use_case, script, profile)
                judgment = judge_voice(audio_path, prompt)

                if judgment:
                    scores = judgment.get("scores", {})
                    scene_scores[sname] = scores
                    scene_totals[sname] = sum(scores.values())
                    for k, v in scores.items():
                        all_scores.setdefault(k, []).append(v)
                    if judgment.get("assessment"):
                        assessment = judgment["assessment"]
                    if judgment.get("concerns"):
                        concerns = judgment["concerns"]
                    total = sum(scores.values())
                    print(f"  [judge] {sname}: {total}/{len(profile['criteria']) * 10}")
                else:
                    print(f"  [judge] {sname}: no judgment returned")

            if not has_audio:
                continue

            criteria_averages = {}
            for c in profile["criteria"]:
                vals = all_scores.get(c, [])
                criteria_averages[c] = sum(vals) / len(vals) if vals else 0

            results.append({
                "id": cid,
                "name": cname,
                "provider": candidate.get("provider"),
                "gender": candidate.get("gender"),
                "search_score": candidate.get("search_score", 0),
                "scene_scores": scene_scores,
                "scene_totals": scene_totals,
                "criteria_averages": criteria_averages,
                "assessment": assessment,
                "concerns": concerns,
            })

    if not results:
        print("\n[audition] No candidates could be auditioned (missing API keys).")
        print("[audition] Add provider API keys to .env and try again.")
        (out_dir / "brief.json").write_text(json.dumps({
            "brief": brief,
            "use_case": use_case,
            "profile": profile,
            "candidates": [{"id": c["id"], "name": c.get("name"), "provider": c.get("provider")} for c in candidates],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, indent=2))
        print(f"[audition] Brief + candidates saved to {out_dir}/brief.json")
        return

    scorecard = format_scorecard(brief, use_case, profile, results, out_dir)
    print()
    print(scorecard)

    # Save results
    (out_dir / "scores.json").write_text(json.dumps(results, indent=2))
    (out_dir / "scorecard.txt").write_text(scorecard)
    (out_dir / "brief.json").write_text(json.dumps({
        "brief": brief,
        "use_case": use_case,
        "profile": profile,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    print(f"\n[audition] Results saved to {out_dir}")
