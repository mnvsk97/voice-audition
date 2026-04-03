# Voice Agent Best Practices

## The Emotional Voice Tradeoff (Deepgram Research)

Emotional/expressive TTS significantly degrades ASR accuracy:
- Entity recognition drops 7-20 percentage points
- WER increases 25-35% vs neutral
- Transcription accuracy: 85% (neutral) → 78% (emotional), severe cases 65-67%

Six mechanisms: pitch variance, tempo variations, formant shifts, prosodic modifications,
training data mismatches, duration modeling failures.

### When emotional voices justify the cost:
- Contact centers: up to 50% CSAT improvement
- Mental health: users rank emotional comfort > transcription accuracy
- Coaching/training: emotional responsiveness creates perceived understanding

### When neutral is non-negotiable:
- Transactional: order confirmation, account verification, financial authorization
- Anywhere entity extraction accuracy matters

### Cost: 4-10x multiplier (up to 40x premium). At 10K concurrent calls 24/7, ~$900K/year difference.

## Latency Benchmarks
| Metric | Target | Source |
|--------|--------|--------|
| Round-trip response | 500-800ms | Pipecat |
| Human turn-taking | <200ms | Retell AI |
| CSAT drop per second of latency | -16% | Retell AI |
| Silence threshold for negative experience | >3 seconds | Retell AI |

## Use-Case Voice Profiles

### Healthcare
- Tone: Professional, empathetic, handles sensitive conversations
- Voice quality: Ultra-realistic neural voices reduce patient anxiety
- Key: perceived age 28-45, moderate pitch, slow-moderate pace, high warmth

### Sales
- Primary driver: Speed. "35-50% of sales go to whoever responds first"
- Natural delivery > branding. Prospects notice latency/interruptions immediately
- Metrics: +23% conversion, +50% leads, 3x profitability per lead with natural voices

### Customer Support
- Goal: Reduce abandonment, increase first-call resolution
- Metrics: Abandonment 12.4% → 2.8% with good voice agents
- Key: Instant response, natural flow, personalization via CRM, context-aware transfers

### Financial Services
- Trust paramount. Voice biometrics cut fraud 50% at HSBC
- Consistency: identical service quality across interactions
- Compliance: automatic logging, regulatory script adherence

## Key Industry Metrics
| Metric | Benchmark |
|--------|-----------|
| Call abandonment (industry avg) | 5.91% |
| AI callback success rate | 95% vs 18% human-only |
| First Call Resolution target | 70-85% (80%+ world-class) |
| AHT reduction with AI | 20-30% |
| Support ticket reduction | 40-60% in first quarter |
| Sales cycle compression | Up to 30% |
| Resolution speed vs human | 12x faster |
| Conversational AI market 2030 | $32.6-49.9B |

## Common Mistakes
1. Choosing expressiveness over accuracy for transactional use cases
2. Ignoring latency — premium 2+ second voices destroy conversation flow
3. One-size-fits-all voice — not varying by use case
4. Skipping A/B testing on voice/tone/pacing
5. Over-engineering emotion at cost of clarity and speed
6. Neglecting accent/dialect diversity in ASR training
7. Verbosity — long responses increase cognitive load
8. Cold/robotic tone in emotionally sensitive contexts
9. Brand-voice mismatch
10. Ignoring accessibility — no volume controls, no speech impairment accommodation
