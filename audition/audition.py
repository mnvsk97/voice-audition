from __future__ import annotations

import asyncio
import json
import os
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
    print(f"[audition] {len(candidates)} candidates found")
    for c in candidates:
        print(f"  {c.get('name', '?')} ({c.get('provider')}) [{c.get('gender', '?')}] score={c.get('search_score', 0):.3f}")
    print()

    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="audition_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save brief + candidates for the skill/MCP to pick up
    (out_dir / "brief.json").write_text(json.dumps({
        "brief": brief,
        "use_case": use_case,
        "profile": profile,
        "candidates": [{"id": c["id"], "name": c.get("name"), "provider": c.get("provider"),
                        "gender": c.get("gender"), "description": c.get("description"),
                        "search_score": c.get("search_score", 0)} for c in candidates],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    print(f"[audition] Results saved to {out_dir}")
