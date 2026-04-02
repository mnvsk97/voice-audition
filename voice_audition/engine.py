"""
Scoring engine that matches requirements against the voice catalog.

Scoring dimensions:
1. Use case fit (hard match + soft match)
2. Brand personality alignment
3. Voice trait similarity (weighted cosine-like)
4. Technical constraints (latency, cost, provider)
5. Demographic preferences (gender, age, accent)
"""

from __future__ import annotations

from .catalog import VOICES
from .models import (
    BrandPersonality, CostTier, LatencyTier, Requirements,
    ScoredVoice, TraitWeights, UseCase, Voice,
)
from .pipecat_config import generate_pipecat_config

# Default trait profiles per use case
USE_CASE_PROFILES: dict[UseCase, TraitWeights] = {
    UseCase.HEALTHCARE: TraitWeights(warmth=0.9, energy=0.2, clarity=0.8, pace=0.2, authority=0.4, friendliness=0.7),
    UseCase.MENTAL_HEALTH: TraitWeights(warmth=1.0, energy=0.1, clarity=0.7, pace=0.1, authority=0.2, friendliness=0.8),
    UseCase.CUSTOMER_SUPPORT: TraitWeights(warmth=0.6, energy=0.4, clarity=0.9, pace=0.5, authority=0.3, friendliness=0.8),
    UseCase.SALES: TraitWeights(warmth=0.5, energy=0.8, clarity=0.8, pace=0.6, authority=0.7, friendliness=0.6),
    UseCase.EDUCATION: TraitWeights(warmth=0.6, energy=0.5, clarity=0.9, pace=0.4, authority=0.5, friendliness=0.7),
    UseCase.FINANCE: TraitWeights(warmth=0.3, energy=0.3, clarity=0.9, pace=0.4, authority=0.9, friendliness=0.3),
    UseCase.HOSPITALITY: TraitWeights(warmth=0.9, energy=0.5, clarity=0.7, pace=0.4, authority=0.3, friendliness=0.9),
    UseCase.LEGAL: TraitWeights(warmth=0.2, energy=0.3, clarity=0.95, pace=0.4, authority=0.9, friendliness=0.2),
    UseCase.REAL_ESTATE: TraitWeights(warmth=0.6, energy=0.7, clarity=0.8, pace=0.5, authority=0.6, friendliness=0.7),
    UseCase.RETAIL: TraitWeights(warmth=0.7, energy=0.7, clarity=0.7, pace=0.6, authority=0.2, friendliness=0.9),
    UseCase.TECH_SUPPORT: TraitWeights(warmth=0.5, energy=0.4, clarity=0.95, pace=0.5, authority=0.4, friendliness=0.6),
    UseCase.FITNESS: TraitWeights(warmth=0.5, energy=0.9, clarity=0.7, pace=0.7, authority=0.5, friendliness=0.7),
    UseCase.GENERAL: TraitWeights(warmth=0.5, energy=0.5, clarity=0.8, pace=0.5, authority=0.5, friendliness=0.5),
}

LATENCY_ORDER = [LatencyTier.FASTEST, LatencyTier.FAST, LatencyTier.STANDARD]
COST_ORDER = [CostTier.LOW, CostTier.MEDIUM, CostTier.HIGH]


def _latency_passes(voice: Voice, max_latency: LatencyTier) -> bool:
    return LATENCY_ORDER.index(voice.latency_tier) <= LATENCY_ORDER.index(max_latency)


def _cost_passes(voice: Voice, max_cost: CostTier) -> bool:
    return COST_ORDER.index(voice.cost_tier) <= COST_ORDER.index(max_cost)


def _use_case_score(voice: Voice, use_case: UseCase) -> float:
    if use_case in voice.best_for:
        return 1.0
    return 0.3  # partial credit — voice may still work


def _personality_score(voice: Voice, personalities: list[BrandPersonality]) -> float:
    if not personalities:
        return 0.5
    matches = sum(1 for p in personalities if p in voice.personality_fit)
    return matches / len(personalities)


def _trait_score(voice: Voice, weights: TraitWeights) -> float:
    """Score how well voice traits match the ideal profile weights.

    For each trait, the weight indicates desired level. We score based on
    how close the voice trait is to the desired level.
    """
    traits = voice.traits
    pairs = [
        (traits.warmth, weights.warmth),
        (traits.energy, weights.energy),
        (traits.clarity, weights.clarity),
        (traits.pace, weights.pace),
        (traits.authority, weights.authority),
        (traits.friendliness, weights.friendliness),
    ]
    total = sum(1.0 - abs(actual - desired) for actual, desired in pairs)
    return total / len(pairs)


def _demographic_score(voice: Voice, req: Requirements) -> float:
    score = 1.0
    penalties = 0
    checks = 0

    if req.gender_preference is not None:
        checks += 1
        if voice.gender != req.gender_preference:
            penalties += 1

    if req.age_preference is not None:
        checks += 1
        if voice.age_range != req.age_preference:
            penalties += 1

    if req.accent is not None:
        checks += 1
        if voice.accent.lower() != req.accent.lower():
            penalties += 1

    if checks == 0:
        return 1.0
    return 1.0 - (penalties / checks)


def score_voice(voice: Voice, req: Requirements) -> ScoredVoice | None:
    # Hard filters
    if not _latency_passes(voice, req.max_latency):
        return None
    if not _cost_passes(voice, req.max_cost):
        return None
    if req.provider_preference and voice.provider != req.provider_preference:
        return None
    if req.language and voice.language != req.language:
        return None

    # Get trait weights from explicit input or use-case default
    trait_weights = req.trait_weights or USE_CASE_PROFILES.get(
        req.use_case, USE_CASE_PROFILES[UseCase.GENERAL]
    )

    # Score components
    use_case = _use_case_score(voice, req.use_case)
    personality = _personality_score(voice, req.brand_personality)
    traits = _trait_score(voice, trait_weights)
    demographic = _demographic_score(voice, req)

    # Weighted final score
    weights = {
        "use_case": 25,
        "personality": 20,
        "traits": 35,
        "demographic": 20,
    }
    raw = (
        use_case * weights["use_case"]
        + personality * weights["personality"]
        + traits * weights["traits"]
        + demographic * weights["demographic"]
    )
    final = round(raw, 1)

    breakdown = {
        "use_case": round(use_case * weights["use_case"], 1),
        "personality": round(personality * weights["personality"], 1),
        "traits": round(traits * weights["traits"], 1),
        "demographic": round(demographic * weights["demographic"], 1),
    }

    return ScoredVoice(
        voice=voice,
        score=final,
        breakdown=breakdown,
        pipecat_config=generate_pipecat_config(voice),
    )


def suggest(req: Requirements, top_n: int = 5) -> list[ScoredVoice]:
    scored = []
    for voice in VOICES:
        result = score_voice(voice, req)
        if result:
            scored.append(result)

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:top_n]
