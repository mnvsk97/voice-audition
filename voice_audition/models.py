from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Provider(str, Enum):
    CARTESIA = "cartesia"
    ELEVENLABS = "elevenlabs"
    DEEPGRAM = "deepgram"
    OPENAI = "openai"
    PLAYHT = "playht"
    AZURE = "azure"
    GOOGLE = "google"
    RIME = "rime"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class AgeRange(str, Enum):
    YOUNG = "young"        # 18-30
    MIDDLE = "middle"      # 30-50
    MATURE = "mature"      # 50+


class UseCase(str, Enum):
    HEALTHCARE = "healthcare"
    CUSTOMER_SUPPORT = "customer_support"
    SALES = "sales"
    EDUCATION = "education"
    FINANCE = "finance"
    HOSPITALITY = "hospitality"
    LEGAL = "legal"
    REAL_ESTATE = "real_estate"
    RETAIL = "retail"
    TECH_SUPPORT = "tech_support"
    MENTAL_HEALTH = "mental_health"
    FITNESS = "fitness"
    GENERAL = "general"


class BrandPersonality(str, Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    EMPATHETIC = "empathetic"
    ENERGETIC = "energetic"
    CALM = "calm"
    LUXURIOUS = "luxurious"
    PLAYFUL = "playful"
    TRUSTWORTHY = "trustworthy"


class LatencyTier(str, Enum):
    FASTEST = "fastest"    # <200ms TTFB
    FAST = "fast"          # 200-500ms TTFB
    STANDARD = "standard"  # 500ms+ TTFB


class CostTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VoiceTraits(BaseModel):
    warmth: float = Field(ge=0, le=1, description="0=cold/clinical, 1=very warm")
    energy: float = Field(ge=0, le=1, description="0=low energy/calm, 1=high energy")
    clarity: float = Field(ge=0, le=1, description="0=soft/breathy, 1=crisp/clear")
    pace: float = Field(ge=0, le=1, description="0=slow, 0.5=moderate, 1=fast")
    authority: float = Field(ge=0, le=1, description="0=casual, 1=authoritative")
    friendliness: float = Field(ge=0, le=1, description="0=neutral/formal, 1=very friendly")


class Voice(BaseModel):
    id: str
    name: str
    provider: Provider
    provider_voice_id: str
    gender: Gender
    age_range: AgeRange
    accent: str = "american"
    language: str = "en"
    traits: VoiceTraits
    latency_tier: LatencyTier
    cost_tier: CostTier
    best_for: list[UseCase]
    personality_fit: list[BrandPersonality]
    description: str
    sample_url: str | None = None


class Requirements(BaseModel):
    use_case: UseCase = UseCase.GENERAL
    brand_personality: list[BrandPersonality] = Field(default_factory=lambda: [BrandPersonality.PROFESSIONAL])
    gender_preference: Gender | None = None
    age_preference: AgeRange | None = None
    language: str = "en"
    accent: str | None = None
    max_latency: LatencyTier = LatencyTier.FAST
    max_cost: CostTier = CostTier.MEDIUM
    provider_preference: Provider | None = None
    trait_weights: TraitWeights | None = None


class TraitWeights(BaseModel):
    """How important each trait is for this use case (0-1)."""
    warmth: float = 0.5
    energy: float = 0.3
    clarity: float = 0.7
    pace: float = 0.3
    authority: float = 0.3
    friendliness: float = 0.5


class ScoredVoice(BaseModel):
    voice: Voice
    score: float = Field(ge=0, le=100)
    breakdown: dict[str, float]
    pipecat_config: str
