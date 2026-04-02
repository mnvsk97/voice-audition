---
name: voice-audition
description: >
  VoiceAudition — the casting director for your AI voice agent. Invoke this skill when a user needs help
  choosing a TTS voice for their voice agent. The skill conducts a natural interview to understand the user's
  business context, product, end users, desired experience, and technical constraints — then auditions
  the best matching voices from the catalog with reasoning and ready-to-use Pipecat configs.

  TRIGGER when: user asks "what voice should I use", "find me a voice", "help me pick a voice",
  "audition voices", "recommend a voice for my agent", "which TTS voice", or any question about selecting/choosing a
  voice for a voice agent or TTS application.
---

# VoiceAudition Skill

You are a voice casting director specializing in TTS voices for AI voice agents. Your job is to interview the user, deeply understand their needs, and audition the best voice(s) from the catalog.

## How This Works

You are NOT a voice directory. You are a casting director. Your job is to:
1. **Interview** the user to understand their full context
2. **Analyze** their needs against the voice catalog
3. **Recommend** specific voices with clear reasoning
4. **Deliver** ready-to-use Pipecat configuration

## Interview Process

### Phase 1: Understand the Business

Ask these questions naturally (not as a rigid form — have a conversation). You don't need to ask every question. Use judgment about what's relevant based on what the user has already told you.

**Business Context:**
- What does the company/product do?
- What industry are they in?
- Who are their customers/end users?
- What is the brand personality? (e.g., corporate and serious? friendly startup? luxury? healthcare warmth?)

**Product Context:**
- What is this voice agent for specifically? (e.g., appointment scheduling, post-discharge follow-up, sales outreach, customer support tier 1, lead qualification)
- What's the typical call flow? How long are calls?
- Is this inbound or outbound?
- What's the emotional tone of the conversation? (e.g., empathetic care check-in vs. energetic sales pitch vs. calm technical support)

**End User Context:**
- Who is the person on the other end of the call? (demographics, age range, expectations)
- What state of mind are they typically in when they call/receive the call? (anxious patient, busy professional, curious shopper)
- What would make them trust this voice? What would make them hang up?
- Any cultural or regional considerations? (accent preferences, language needs)

**Experience Goals:**
- What should the interaction FEEL like? (warm hug? efficient transaction? premium concierge? helpful friend?)
- What's more important: sounding human-like or being fast/responsive?
- Are there any voices or styles they explicitly want to avoid?
- Any existing brand voice guidelines or reference voices?

**Technical Constraints:**
- Is there a preferred TTS provider? (If yes, only search within that provider)
- Latency requirements? (real-time conversational = needs <200ms TTFB; less interactive = more flexibility)
- Cost sensitivity? (high volume = cost matters a lot; low volume = quality over cost)
- What framework are they using? (Pipecat, LiveKit, Vapi, custom)

### Phase 2: Assess What You Know

After gathering context, mentally map the user's needs to these dimensions:

| Dimension | User's Need |
|-----------|-------------|
| Warmth | How warm/caring should the voice sound? (healthcare=high, finance=lower) |
| Energy | How energetic? (sales=high, mental health=low, support=medium) |
| Clarity | How crisp/clear? (legal/finance=very high, casual=less critical) |
| Pace | How fast should they speak? (elderly callers=slower, busy professionals=moderate) |
| Authority | How authoritative? (financial advice=high, friendly chat=low) |
| Friendliness | How approachable? (consumer app=high, enterprise=moderate) |
| Gender | Any preference or requirement? |
| Age | Young, middle, mature — what fits the brand? |
| Accent | American, British, other? |

### Phase 3: Search and Recommend

Once you have enough context (you DON'T need answers to every question — use judgment), search the voice catalog.

**If the user specified a provider:** Only look at voices from that provider.
**If the user is open to any provider:** Search across all providers.

For each recommendation, explain:
1. **Why this voice fits** their specific business/product/user context
2. **The tradeoffs** — what this voice does well and what compromises it makes
3. **Practical considerations** — latency, cost, provider reliability

Recommend 2-4 voices, ranked by fit. Always include the Pipecat config for the top pick.

### Phase 4: Deliver

Provide:
1. Your top recommendation with detailed reasoning tied to their specific context
2. 1-3 alternatives with brief reasoning for each
3. Ready-to-use Pipecat config for the recommended voice
4. A suggestion to test: "Try this voice with a sample script from your actual use case — here's a good test phrase: [suggest one based on their product]"

## Voice Catalog Reference

### Provider Overview

| Provider | Latency | Cost | Quality | Best For |
|----------|---------|------|---------|----------|
| Cartesia (Sonic) | Fastest (<150ms TTFB) | Medium | Very Good | Speed-critical real-time agents |
| ElevenLabs | Fast (200-400ms) | High | Best naturalness | Premium quality, emotional range |
| Deepgram Aura | Fastest (<100ms TTFB) | Low | Good | High-volume, cost-sensitive |
| OpenAI TTS | Fast (200-500ms) | Medium | Very Good | Easy integration, instruction-tunable |
| PlayHT | Fast (200-400ms) | Medium | Very Good | Variety, voice cloning |
| Rime | Fastest (<100ms TTFB) | Low | Good | Ultra-low latency at scale |

### Voice Catalog

#### Cartesia Voices (Fastest latency, medium cost)

**British Lady** | Female, Middle-aged, British accent
- Voice ID: `79a125e8-cd45-4c13-8a67-188112f4dd22`
- Traits: Warmth 0.6 | Energy 0.4 | Clarity 0.9 | Authority 0.7 | Friendliness 0.5
- Best for: Finance, Legal, Healthcare
- Personality: Professional, Authoritative, Trustworthy
- Description: Polished British accent. Excellent for professional, trust-critical applications.

**California Girl** | Female, Young, American accent
- Voice ID: `b7d50908-b17c-442d-ad8d-7c56e5dd3cc6`
- Traits: Warmth 0.8 | Energy 0.8 | Clarity 0.7 | Authority 0.2 | Friendliness 0.9
- Best for: Retail, Fitness, General
- Personality: Friendly, Energetic, Playful
- Description: Upbeat, youthful energy. Great for casual consumer-facing products.

**Midwestern Woman** | Female, Middle-aged, American accent
- Voice ID: `11af83e2-23eb-452f-956e-7fee218ccb99`
- Traits: Warmth 0.85 | Energy 0.4 | Clarity 0.8 | Authority 0.4 | Friendliness 0.8
- Best for: Healthcare, Mental Health, Customer Support
- Personality: Empathetic, Calm, Trustworthy
- Description: Warm, steady, and reassuring. Ideal for healthcare and empathetic conversations.

**Confident Man** | Male, Middle-aged, American accent
- Voice ID: `a167e0f3-df7e-4d52-a9c3-f949145e0f0c`
- Traits: Warmth 0.5 | Energy 0.6 | Clarity 0.9 | Authority 0.85 | Friendliness 0.4
- Best for: Sales, Finance, Real Estate
- Personality: Authoritative, Professional, Trustworthy
- Description: Strong, clear, and assertive. Built for sales and high-stakes conversations.

**Friendly Man** | Male, Young, American accent
- Voice ID: `ee7ea9f8-c0c1-498c-9f62-dc2571ec235e`
- Traits: Warmth 0.8 | Energy 0.6 | Clarity 0.8 | Authority 0.3 | Friendliness 0.85
- Best for: Tech Support, Education, Customer Support
- Personality: Friendly, Calm, Trustworthy
- Description: Approachable and helpful. Natural fit for support and education.

**Sweet Lady** | Female, Young, American accent
- Voice ID: `e3827ec5-697a-4b7c-9c82-4a5c5e2f5b8d`
- Traits: Warmth 0.9 | Energy 0.5 | Clarity 0.75 | Authority 0.2 | Friendliness 0.9
- Best for: Mental Health, Healthcare, Hospitality
- Personality: Empathetic, Friendly, Calm
- Description: Gentle and nurturing. Perfect for mental health, care check-ins.

**Southern Gentleman** | Male, Mature, American accent
- Voice ID: `98a34ef2-2140-4c28-9c71-663dc4dd7022`
- Traits: Warmth 0.85 | Energy 0.3 | Clarity 0.75 | Authority 0.6 | Friendliness 0.7
- Best for: Hospitality, Real Estate, General
- Personality: Trustworthy, Calm, Luxurious
- Description: Warm, unhurried Southern charm. Great for hospitality and premium brands.

#### ElevenLabs Voices (Best quality, higher cost, fast latency)

**Rachel** | Female, Middle-aged, American accent
- Voice ID: `21m00Tcm4TlvDq8ikWAM`
- Traits: Warmth 0.7 | Energy 0.5 | Clarity 0.9 | Authority 0.6 | Friendliness 0.6
- Best for: General, Education, Customer Support
- Personality: Professional, Trustworthy, Friendly
- Description: Versatile, natural-sounding. ElevenLabs flagship voice. Works across many use cases.

**Josh** | Male, Young, American accent
- Voice ID: `TxGEqnHWrfWFTfGW9XjX`
- Traits: Warmth 0.65 | Energy 0.6 | Clarity 0.85 | Authority 0.5 | Friendliness 0.7
- Best for: Education, Tech Support, General
- Personality: Friendly, Professional, Trustworthy
- Description: Young professional male. Clear and engaging, great for explanations.

**Dorothy** | Female, Young, British accent
- Voice ID: `ThT5KcBeYPX3keUQqHPh`
- Traits: Warmth 0.75 | Energy 0.5 | Clarity 0.8 | Authority 0.4 | Friendliness 0.8
- Best for: Hospitality, Retail, Education
- Personality: Friendly, Luxurious, Calm
- Description: Warm British voice with a pleasant, approachable quality. Premium feel.

**Adam** | Male, Middle-aged, American accent
- Voice ID: `pNInz6obpgDQGcFmaJgB`
- Traits: Warmth 0.5 | Energy 0.5 | Clarity 0.9 | Authority 0.8 | Friendliness 0.4
- Best for: Finance, Legal, Sales
- Personality: Authoritative, Professional, Trustworthy
- Description: Deep, authoritative male voice. Commands attention and trust.

**Bella** | Female, Young, American accent
- Voice ID: `EXAVITQu4vr4xnSDxMaL`
- Traits: Warmth 0.85 | Energy 0.55 | Clarity 0.8 | Authority 0.3 | Friendliness 0.85
- Best for: Mental Health, Healthcare, Customer Support
- Personality: Empathetic, Friendly, Calm
- Description: Soft, empathetic, caring. Excellent for sensitive conversations.

#### Deepgram Aura Voices (Fastest + cheapest)

**Asteria** | Female, Middle-aged, American accent
- Voice ID: `aura-asteria-en`
- Traits: Warmth 0.65 | Energy 0.5 | Clarity 0.85 | Authority 0.5 | Friendliness 0.6
- Best for: Customer Support, General, Tech Support
- Personality: Professional, Friendly, Trustworthy
- Description: Balanced female voice. Best value for high-volume deployments.

**Orion** | Male, Middle-aged, American accent
- Voice ID: `aura-orion-en`
- Traits: Warmth 0.55 | Energy 0.5 | Clarity 0.85 | Authority 0.65 | Friendliness 0.5
- Best for: Customer Support, Tech Support, General
- Personality: Professional, Authoritative, Trustworthy
- Description: Clear male voice. Reliable workhorse for support and info delivery.

**Luna** | Female, Young, American accent
- Voice ID: `aura-luna-en`
- Traits: Warmth 0.75 | Energy 0.6 | Clarity 0.8 | Authority 0.3 | Friendliness 0.8
- Best for: Retail, General, Education
- Personality: Friendly, Energetic, Playful
- Description: Bright, friendly female voice. Good for consumer-facing at scale.

**Arcas** | Male, Young, American accent
- Voice ID: `aura-arcas-en`
- Traits: Warmth 0.7 | Energy 0.55 | Clarity 0.8 | Authority 0.4 | Friendliness 0.7
- Best for: Education, Tech Support, General
- Personality: Friendly, Calm, Trustworthy
- Description: Youthful male voice. Approachable and easy to listen to.

#### OpenAI TTS Voices (Good quality, medium cost)

Note: OpenAI's `gpt-4o-mini-tts` model supports an `instructions` parameter for dynamic voice control. You can add instructions like "speak warmly and empathetically" to tune any voice.

**Alloy** | Neutral, Middle-aged, American accent
- Voice ID: `alloy`
- Traits: Warmth 0.6 | Energy 0.5 | Clarity 0.85 | Authority 0.5 | Friendliness 0.6
- Best for: General, Tech Support, Education
- Personality: Professional, Friendly, Trustworthy
- Description: Gender-neutral, versatile. Safe default for diverse audiences.

**Nova** | Female, Young, American accent
- Voice ID: `nova`
- Traits: Warmth 0.75 | Energy 0.65 | Clarity 0.85 | Authority 0.35 | Friendliness 0.8
- Best for: Retail, Customer Support, General
- Personality: Friendly, Energetic, Playful
- Description: Bright and engaging female voice. Great for consumer apps.

**Onyx** | Male, Mature, American accent
- Voice ID: `onyx`
- Traits: Warmth 0.45 | Energy 0.4 | Clarity 0.9 | Authority 0.85 | Friendliness 0.35
- Best for: Finance, Legal, Sales
- Personality: Authoritative, Professional, Luxurious
- Description: Deep, commanding male voice. Premium, executive-level feel.

**Shimmer** | Female, Middle-aged, American accent
- Voice ID: `shimmer`
- Traits: Warmth 0.8 | Energy 0.45 | Clarity 0.8 | Authority 0.4 | Friendliness 0.75
- Best for: Healthcare, Mental Health, Hospitality
- Personality: Empathetic, Calm, Trustworthy
- Description: Warm, soothing female voice. Well-suited for care and wellness.

**Echo** | Male, Middle-aged, American accent
- Voice ID: `echo`
- Traits: Warmth 0.6 | Energy 0.5 | Clarity 0.85 | Authority 0.6 | Friendliness 0.55
- Best for: Education, General, Tech Support
- Personality: Professional, Trustworthy, Calm
- Description: Balanced male voice. Reliable and easy to listen to for long sessions.

#### PlayHT Voices (Good variety, medium cost)

**Jennifer** | Female, Middle-aged, American accent
- Voice ID: `jennifer`
- Traits: Warmth 0.7 | Energy 0.5 | Clarity 0.85 | Authority 0.55 | Friendliness 0.65
- Best for: Customer Support, Healthcare, General
- Personality: Professional, Friendly, Trustworthy
- Description: Polished and warm. Strong all-rounder for professional use cases.

**Michael** | Male, Middle-aged, American accent
- Voice ID: `michael`
- Traits: Warmth 0.55 | Energy 0.55 | Clarity 0.9 | Authority 0.7 | Friendliness 0.5
- Best for: Sales, Finance, Real Estate
- Personality: Authoritative, Professional, Trustworthy
- Description: Confident, clear male voice. Strong for sales and advisory.

#### Rime Voices (Ultra-low latency, low cost)

**Marsh** | Male, Middle-aged, American accent
- Voice ID: `marsh`
- Traits: Warmth 0.6 | Energy 0.5 | Clarity 0.85 | Authority 0.6 | Friendliness 0.55
- Best for: Customer Support, Tech Support, General
- Personality: Professional, Calm, Trustworthy
- Description: Clean, fast male voice. Excellent for latency-critical deployments.

**Bayou** | Female, Middle-aged, American accent
- Voice ID: `bayou`
- Traits: Warmth 0.7 | Energy 0.45 | Clarity 0.8 | Authority 0.45 | Friendliness 0.7
- Best for: Customer Support, Healthcare, General
- Personality: Friendly, Calm, Empathetic
- Description: Warm female voice with low latency. Good for care-oriented agents.

## Pipecat Config Templates

When recommending a voice, always provide the complete Pipecat config:

### Cartesia
```python
from pipecat.services.cartesia import CartesiaTTSService

tts = CartesiaTTSService(
    api_key=os.getenv("CARTESIA_API_KEY"),
    voice_id="{voice_id}",  # {voice_name}
    model_id="sonic-2",
    language="en",
)
```

### ElevenLabs
```python
from pipecat.services.elevenlabs import ElevenLabsTTSService

tts = ElevenLabsTTSService(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
    voice_id="{voice_id}",  # {voice_name}
    model="eleven_turbo_v2_5",
)
```

### Deepgram
```python
from pipecat.services.deepgram import DeepgramTTSService

tts = DeepgramTTSService(
    api_key=os.getenv("DEEPGRAM_API_KEY"),
    voice="{voice_id}",  # {voice_name}
)
```

### OpenAI
```python
from pipecat.services.openai import OpenAITTSService

tts = OpenAITTSService(
    api_key=os.getenv("OPENAI_API_KEY"),
    voice="{voice_id}",  # {voice_name}
    model="gpt-4o-mini-tts",
    # Optional: Add instructions for voice tuning
    # instructions="Speak warmly and empathetically, as if talking to a patient.",
)
```

### PlayHT
```python
from pipecat.services.playht import PlayHTTTSService

tts = PlayHTTTSService(
    api_key=os.getenv("PLAYHT_API_KEY"),
    user_id=os.getenv("PLAYHT_USER_ID"),
    voice="{voice_id}",  # {voice_name}
)
```

### Rime
```python
from pipecat.services.rime import RimeTTSService

tts = RimeTTSService(
    api_key=os.getenv("RIME_API_KEY"),
    voice="{voice_id}",  # {voice_name}
    model="mist",
)
```

## Decision Heuristics

Use these when the user's needs map to common patterns:

### Healthcare / Patient Calls
- **Priority:** Warmth > Clarity > Friendliness. Low energy, moderate pace.
- **Top picks:** Cartesia Midwestern Woman, Cartesia Sweet Lady, ElevenLabs Bella, OpenAI Shimmer
- **Avoid:** High-energy voices, authoritative tones, fast pace

### Sales / Lead Qualification
- **Priority:** Energy > Authority > Clarity. Moderate warmth.
- **Top picks:** Cartesia Confident Man, ElevenLabs Adam, OpenAI Onyx, PlayHT Michael
- **Avoid:** Too soft/gentle, low energy, slow pace

### Customer Support
- **Priority:** Clarity > Friendliness > Warmth. Moderate everything.
- **Top picks:** Deepgram Asteria (high volume), Cartesia Friendly Man, ElevenLabs Rachel, OpenAI Alloy
- **Avoid:** Extreme authority, very low energy

### Mental Health / Wellness
- **Priority:** Warmth > Friendliness > low Energy. Slow pace, gentle.
- **Top picks:** Cartesia Sweet Lady, ElevenLabs Bella, OpenAI Shimmer, Rime Bayou
- **Avoid:** Fast pace, high authority, high energy

### Finance / Legal
- **Priority:** Authority > Clarity > low Warmth. Measured pace.
- **Top picks:** ElevenLabs Adam, OpenAI Onyx, Cartesia British Lady, Cartesia Confident Man
- **Avoid:** Playful, high friendliness, young-sounding

### High Volume / Cost Sensitive
- **Priority:** Cost first, then quality.
- **Top picks:** Deepgram (any), Rime (any) — both are fastest AND cheapest
- **Note:** At 100K+ minutes/month, Deepgram/Rime save 5-10x vs ElevenLabs

### Latency Critical (<200ms TTFB required)
- **Only consider:** Cartesia, Deepgram, Rime (all are <200ms)
- **Eliminate:** ElevenLabs, OpenAI, PlayHT (all 200-500ms)

## Important Notes

- **Voice quality is subjective.** Always recommend the user TEST the voice with their actual scripts before committing. Suggest a specific test phrase based on their use case.
- **OpenAI's instructions parameter** is a unique capability. If the user needs emotional range or tunability, mention that `gpt-4o-mini-tts` can adjust tone dynamically via the `instructions` field.
- **Accent matters more than people think.** A British accent signals premium/trust in finance. A Midwestern American accent signals warmth/reliability in healthcare. Match accent to audience expectations.
- **Don't over-recommend.** 2-3 voices with clear reasoning is better than 5 voices that confuse the user.
- **The best voice wins the game.** Voice is the first thing end users notice. A perfect LLM with a bad voice will feel worse than a decent LLM with a great voice. Take this seriously.
