# VoiceAudition PRD
## The Voice Casting Director for AI Agents

**Author:** Voice Agent Agency | **Date:** April 2026 | **Version:** 1.0

---

## 1. Executive Summary

**Problem:** There are 15+ TTS providers with 12,000+ voices combined. No tool exists to discover, compare, test, and select the right voice across providers. Developers spend 2-8 hours manually browsing provider dashboards for each project. There is zero cross-provider comparison tooling in the market.

**Solution:** VoiceAudition — the definitive platform for discovering and selecting AI voices across every provider. A unified voice index with normalized metadata, side-by-side audio comparison, latency benchmarks, cost modeling, and drop-in Pipecat integration.

**Positioning:** "The Wirecutter for AI Voices" / "Postman for TTS"

**Why now:**
- Voice agent market is $19.2B (2025), growing 23% CAGR to $155B by 2035
- TTS market fragmenting rapidly (25+ providers, each with unique catalogs)
- 500K+ developers on Vapi alone; Pipecat at 11K GitHub stars, 604K monthly downloads
- ElevenLabs just raised at $11B, Deepgram at $1.3B, LiveKit at $1B — the ecosystem is exploding
- **Nobody is solving voice discovery.** Zero direct competitors.

**Target:** $5-15M ARR by Year 3

---

## 2. Market Analysis

### 2.1 Market Size

| Market | 2025 Size | Projected | CAGR |
|--------|-----------|-----------|------|
| TTS | $3.9B | $7.9B (2031) | 12.7% |
| Conversational AI | $19.2B | $155B (2035) | 23.2% |
| Cloud Contact Centers | $36B | $86.4B (2029) | 26.9% |
| **Combined TAM** | **$24-30B** | | |
| **SAM (voice tooling)** | **$200-500M** | | |
| **SOM (Year 3)** | **$5-15M** | | |

### 2.2 Developer Ecosystem Size

| Platform | Reach |
|----------|-------|
| Vapi | 500K+ registered developers, 300M+ calls processed |
| LiveKit Agents | 300K+ developers, 2.86M monthly PyPI downloads |
| Pipecat | 11K GitHub stars, 604K monthly downloads, 225+ contributors |
| Voiceflow | 200K+ users, 10K+ live agents |
| GitHub "voice agent" repos | 15,595 repositories |

**Estimated active voice agent developers: 200K-400K globally**
**Estimated companies building voice agents: 5,000-15,000**

### 2.3 Competitive Landscape

| Category | Players | Gap |
|----------|---------|-----|
| Model-level benchmarks | Artificial Analysis, TTS Arena | Compares engines, not individual voices |
| Single-provider libraries | ElevenLabs Voice Library, Cartesia Playground | One provider only |
| Voice agent platforms | Retell, Vapi, Bland | Voice selection is a dropdown afterthought |
| Voice branding agencies | amp Sound Branding | $100K+ engagements, not self-serve |
| **Cross-provider voice selection** | **NOBODY** | **This is the gap** |

---

## 3. User Personas

### 3.1 Primary (Build For First)

**P1: Voice AI Developer** ("Dev Darshan")
- Senior engineer building with Pipecat/LiveKit/Vapi
- Spends 2-8 hours per project browsing provider dashboards
- Wants: side-by-side comparison, latency benchmarks, Pipecat config export
- WTP: $29-99/mo
- **Where:** HN, GitHub, Discord, Dev Twitter

**P2: AI Agency Founder** ("Agency Anika")
- Runs a voice AI agency, builds agents for multiple clients
- Repeats voice selection for every client with no professional presentation tools
- Wants: branded comparison reports, batch testing, white-label voice demos
- WTP: $79-299/mo
- **Where:** Twitter/X, LinkedIn, agency communities

### 3.2 Secondary (Expand To)

**P3: Product Manager** at a company deploying voice agents
- Non-technical, needs to justify voice choice to stakeholders
- Wants: comparison reports, recommendation rationale, A/B test results
- WTP: $79-199/mo (team plan)

**P4: CX/Contact Center Leader**
- VP of CX evaluating voice AI for their contact center
- Wants: enterprise voice branding, compliance-safe voices, ROI data
- WTP: $299-999/mo (enterprise)

### 3.3 Tertiary (Future Expansion)

- Content creators (podcasts, audiobooks) — massive volume for SEO
- Game developers (NPC voices)
- E-learning producers
- Accessibility tool builders

### 3.4 Key Pain Points (Validated from Community Research)

1. **No cross-provider comparison tool exists** — the #1 universal complaint
2. **Latency data is never published** in comparable format across providers
3. **Cost modeling is impossible** — per-char vs per-second vs per-request pricing
4. **Demo text doesn't match production context** — "quick brown fox" != appointment scheduling
5. **Voice sounds great in 10s demo, terrible at scale** — uncanny valley over time
6. **60-70% of managed platform spend goes to platform fees** — devs want raw provider economics
7. **Agency builders repeat voice curation for every client** with no professional tools

---

## 4. Product Vision

### 4.1 One-Liner

**Find the perfect voice for your AI agent in minutes, not hours.**

### 4.2 Core Value Propositions

1. **Unified Voice Index** — 12,000+ voices across 9 providers, normalized metadata, one search
2. **Intelligent Matching** — Input your use case, brand, and constraints; get ranked recommendations
3. **Side-by-Side Testing** — Same text, same playback, different providers. Real latency numbers.
4. **Pipecat-Ready** — One click to copy the exact config snippet for your pipeline
5. **Cost Calculator** — True apples-to-apples cost comparison across providers at your volume

### 4.3 Product Principles

- **Provider-agnostic** — We never favor one provider. Objective comparison builds trust.
- **Developer-first** — CLI and API before GUI. Code snippets, not PDFs.
- **Data-driven** — Latency benchmarks, quality scores, community ratings. Not vibes.
- **Fast to value** — First useful result in under 60 seconds.

---

## 5. Feature Specification

### 5.1 Phase 1: Foundation (Weeks 1-6) — MVP

#### F1: Unified Voice Catalog
- Ingest voices from ElevenLabs (11,300+), PlayHT, Rime (562), Deepgram (91), OpenAI (13), Azure (500+), Google, Polly
- Normalize metadata into unified schema (gender, age, accent, language, style tags, use cases)
- Auto-enrich sparse providers via LLM classification (cost: <$10 one-time)
- Total indexed voices: ~12,500+

#### F2: Voice Browser (Web)
- Faceted search: provider, gender, age, accent, language, style, use case, latency tier, cost tier
- Semantic natural-language search: "warm friendly female voice for healthcare"
- Audio preview playback (3 standardized samples per voice: short greeting, narrative, conversational)
- Voice detail page with full metadata, trait radar chart, Pipecat config

#### F3: Voice Recommendation Engine
- Input: use case, brand personality, technical constraints (latency, cost, provider)
- Output: ranked list with scores and breakdown (why this voice scored high)
- Default trait profiles per use case (healthcare=high warmth, sales=high energy, etc.)
- Override weights for custom requirements

#### F4: CLI Tool (Open Source)
- `voice-audition interview` — guided voice selection flow
- `voice-audition quick healthcare --personality empathetic,calm`
- `voice-audition voices --provider cartesia`
- `voice-audition compare <voice1> <voice2>` — side-by-side in terminal
- Publish to PyPI: `pip install voice-audition`

#### F5: Pipecat Config Generator
- For every voice, generate copy-pasteable Pipecat service config
- Full pipeline template (STT + LLM + TTS) for the selected voice
- Support all 8 Pipecat TTS service classes

### 5.2 Phase 2: Intelligence (Weeks 7-12)

#### F6: Side-by-Side A/B Comparison
- Select 2+ voices from any providers
- Play same text simultaneously (synchronized playback)
- Visual waveform comparison
- Custom text input — test with YOUR actual scripts
- Share comparison via URL

#### F7: Latency Benchmarks
- Automated weekly TTFA (time-to-first-audio) measurement from 3 regions
- Real-time latency display per voice
- Filter voices by latency budget (e.g., "only show <200ms TTFB")
- Historical latency trends

#### F8: Cost Calculator
- Input: expected call volume (minutes/month), average call duration
- Output: monthly cost per provider at your volume, with breakdowns
- Normalize per-char, per-second, per-request pricing to per-minute
- Show total stack cost (STT + LLM + TTS + telephony)

#### F9: Community Ratings & Reviews
- Authenticated users rate voices (quality, naturalness, consistency)
- Use-case-specific ratings ("How good is this voice for healthcare?")
- Community-submitted voice descriptions and tags
- Popularity signals (most compared, most selected)

### 5.3 Phase 3: Platform (Weeks 13-24)

#### F10: Embeddable Voice Recommendation API
- REST API for platforms to embed voice selection in their products
- `POST /api/v1/suggest` — programmatic voice recommendation
- `GET /api/v1/voices?gender=female&use_case=healthcare&max_latency=200`
- SDKs for Python and TypeScript

#### F11: Voice A/B Testing at Scale
- Deploy 2 voices in a Pipecat agent, split traffic 50/50
- Track user satisfaction metrics (call duration, completion rate, sentiment)
- Statistical significance reporting
- Integration with Pipecat analytics

#### F12: Enterprise Voice Branding
- Define brand voice guidelines (tone, warmth, energy targets)
- Auto-match new voices to brand profile as catalog updates
- Multi-channel voice consistency monitoring
- Compliance tagging (HIPAA-safe, finance-appropriate)

#### F13: Voice Preview with Custom Instructions (OpenAI)
- Leverage `gpt-4o-mini-tts` instructions parameter
- Generate "virtual voice variants" from 13 base voices
- e.g., "Alloy + empathetic healthcare tone" as a distinct searchable option
- Preview instruction variants side-by-side

---

## 6. Technical Architecture

### 6.1 System Overview

```
                    CLIENT (Next.js)
                         |
                    API (FastAPI)
                    /    |    \
            PostgreSQL  Typesense  Provider Adapters
            (source of  (search    (ElevenLabs, Cartesia,
             truth)     index)     Deepgram, OpenAI, PlayHT,
                                   Rime, Azure, Google, Polly)
                                        |
                                   Cloudflare R2
                                   (audio previews CDN)
```

### 6.2 Key Technology Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| API | FastAPI (Python) | Async, typed, same ecosystem as Pipecat |
| Database | PostgreSQL 16 + pgvector | JSONB for provider metadata, vector search |
| Search | Typesense | Built-in vector + faceted + keyword search. Sub-35ms on 12K docs |
| Storage | Cloudflare R2 | S3-compatible, zero egress fees. 5.6GB audio = $0.09/mo |
| Frontend | Next.js 14 | SSR for SEO on voice pages |
| Task Queue | Celery + Redis | Sync jobs, preview generation, benchmarks |
| Audio Player | Howler.js | Cross-browser Web Audio API |

### 6.3 Voice Metadata Coverage (What We Get vs. Generate)

| Field | ElevenLabs | PlayHT | Azure | Others |
|-------|:----------:|:------:|:-----:|:------:|
| gender | from API | from API | from API | LLM-generated |
| age | from API | from API | -- | LLM-generated |
| accent | from API | from API | via locale | LLM-generated |
| style/tags | from API | from API | StyleList | LLM-generated |
| use_case | from API | from API | -- | LLM-generated |
| preview audio | free URL | free URL | -- | Generated ($0.002/voice) |
| latency | -- | -- | -- | Benchmarked weekly |
| popularity | from API | -- | -- | Community signals |

**Enrichment cost for all sparse providers: <$10 one-time (Claude Haiku batch API)**

### 6.4 Sync Strategy

| Provider | Frequency | Method |
|----------|-----------|--------|
| ElevenLabs | Every 6 hours | API polling (high community churn) |
| PlayHT | Daily | API polling |
| Azure, Google, Rime | Weekly | API/JSON polling |
| Polly, Deepgram, OpenAI | Monthly | Manual + API |

Never delete voices — mark deprecated with nearest-neighbor alternatives.

### 6.5 Infrastructure Costs

| Category | Monthly |
|----------|---------|
| Servers (Railway/Fly) | $10-20 |
| PostgreSQL (Neon/Supabase) | $0-25 |
| Typesense Cloud | $0 (free tier) |
| Cloudflare R2 (5.6GB) | $0.09 |
| Redis (Upstash) | $0 |
| Provider API costs (sync + testing) | $25-65 |
| **Total** | **$40-120/mo** |

---

## 7. Business Model

### 7.1 Recommended Strategy: Open Core + Freemium SaaS + Affiliate + API

**Phased approach, layering revenue streams:**

### 7.2 Pricing

| Tier | Price | Includes |
|------|-------|----------|
| **Free** | $0 | Browse all voices, 20 previews/day, basic filters, CLI tool |
| **Pro** | $29/mo | Unlimited previews, A/B comparison, recommendations, cost calculator, 500 API calls/mo |
| **Team** | $79/mo (3 seats) | Shared libraries, comparison reports, 5K API calls/mo |
| **Enterprise** | $299-999/mo | Brand voice guidelines, SSO, custom scoring, unlimited API |
| **API** | $99-499/mo | Embeddable voice recommendation for platforms |

### 7.3 Additional Revenue Streams

- **Affiliate commissions**: 15-25% from TTS providers for referred signups
- **Featured listings**: $500-2K/mo for providers to get promoted placement
- **Consulting**: $2.5K-5K per voice audit (early revenue, customer discovery)
- **Data/insights**: Voice quality benchmarks, market intelligence (Year 2+)

### 7.4 Unit Economics

| Tier | Revenue | COGS | Gross Margin |
|------|---------|------|-------------|
| Free | $0 | $0.50/mo | -100% |
| Pro | $29/mo | $5/mo | 83% |
| Team | $79/mo | $8/mo | 90% |
| Enterprise | $299/mo | $15/mo | 95% |

**Break-even (excluding salaries): 51 Pro subscribers**
**Break-even (with 2 founders at $10K/mo each): 862 Pro or 316 Team subscribers**

### 7.5 Revenue Projections

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Free users | 10K | 50K | 150K |
| Paid users | 300 | 2K | 8K |
| Monthly revenue | $15K | $160K | $790K |
| **ARR** | **$180K** | **$1.9M** | **$9.5M** |
| Team size | 2 | 6 | 15 |

---

## 8. Go-to-Market Strategy

### 8.1 Phase 1: Developer Adoption (Months 1-6)

**Launch channels:**
1. **Open source CLI** → PyPI, GitHub stars, HN Show launch
2. **Content marketing** → "ElevenLabs vs Cartesia vs Deepgram" benchmark posts (SEO)
3. **Pipecat ecosystem** → Plugin, contributor, Discord presence
4. **Monthly Voice Quality Index** → Benchmark report, becomes authoritative reference

**Targets:** 5K free users, 200 paid, $13K/mo revenue, 1K GitHub stars

### 8.2 Phase 2: Product-Led Growth (Months 6-12)

**Viral mechanics:**
- Shareable comparison links ("Share your voice comparison")
- Embeddable voice preview widget
- "Find your perfect AI voice" quiz (viral content)
- "Powered by VoiceAudition" badge on voice agent demos

**Integration flywheel:**
- `pip install pipecat-voice-audition` plugin
- LiveKit Agents integration
- VS Code extension for voice preview while coding

**Targets:** 20K free users, 1K paid, $95K/mo revenue

### 8.3 Phase 3: Enterprise Expansion (Months 12-24)

- Outbound sales to contact center companies
- SOC2 compliance
- Voice branding workshops
- Channel partnerships with AI agencies (white-label)
- Case studies from Phase 1/2 customers

**Targets:** 100K free users, 5K paid, 20 enterprise, $500K/mo revenue

### 8.4 Key Content Plays

| Content | Purpose | SEO Value |
|---------|---------|-----------|
| "Best TTS Voices for [Industry] in 2026" | Top-of-funnel | High |
| "ElevenLabs vs Cartesia: Voice Quality Benchmark" | Comparison shoppers | Very High |
| "How to Choose a Voice for Your AI Agent" | Education | High |
| Monthly Voice Quality Index | Authority building | High |
| "Voice Agent Tutorial with Perfect Voice in 10 Min" | Developer adoption | Medium |

---

## 9. Partnership Strategy

### 9.1 TTS Providers

| Partner | Value to Them | Value to Us |
|---------|---------------|-------------|
| ElevenLabs | Customer acquisition channel | Revenue share, co-marketing |
| Cartesia | Exposure to voice agent devs | Reduced API costs |
| Deepgram | Discovery for their TTS (less known) | Free API access |
| Rime | Visibility (newer provider) | Unique catalog access |

**Pitch:** "We send you qualified, high-intent customers who've already compared voices and chosen yours."

### 9.2 Voice Agent Platforms

| Partner | Integration |
|---------|------------|
| Pipecat | SDK plugin, voice selector in setup flow |
| LiveKit | Agents marketplace widget |
| Vapi | Embedded recommendation in dashboard |
| Retell | Voice comparison in their builder |

### 9.3 AI Agencies

- White-label platform ($200-500/mo)
- Bulk voice consulting ($2K-5K per project)
- 20% referral commission program

---

## 10. Moat & Defensibility

### 10.1 Compounding Advantages (strongest first)

1. **Data flywheel** — Every comparison generates preference data. The recommendation engine gets smarter with scale. This is nearly impossible to replicate without the same volume.

2. **Community content** — Voice reviews, ratings, use-case-specific feedback. Like G2's review moat — takes years to build.

3. **Integration stickiness** — Once embedded in 10+ platforms (Pipecat, LiveKit, Vapi), switching costs are high.

4. **Metadata database** — Normalized, enriched voice metadata across 9 providers is a massive manual+automated effort. First mover advantage.

5. **Brand trust** — Becoming the authoritative, objective source for voice comparison. Trust compounds.

### 10.2 Why Competitors Won't Build This

- **TTS providers** won't objectively compare against themselves
- **Voice agent platforms** (Vapi, Retell) are focused on their core product, not tooling
- **G2/Capterra** are too generic, not technical enough for developer tooling
- **A new startup** would need 12+ months to build the catalog, enrichment, and community we'll have

---

## 11. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| TTS providers block API access | Medium | High | Negotiate partnerships early; cache aggressively; use official APIs within terms |
| Voice agent platform builds this feature | Medium | Medium | Move fast; be provider-agnostic (they won't be); build data moat |
| Low free-to-paid conversion | Medium | Medium | Focus on team/enterprise features; ensure free tier is useful but limited |
| Market too niche | Low | High | Expand to content creators, game devs, e-learning (500K+ addressable) |
| Voice cloning reduces need for selection | Medium | Medium | Add custom voice comparison/quality scoring; cloning still needs a starting voice |
| TTS pricing race to bottom | Low | Medium | Value is in comparison/recommendation, not TTS itself |

---

## 12. Success Metrics

### 12.1 North Star Metric
**Voices compared per week** — measures core product engagement and data flywheel velocity

### 12.2 Phase 1 KPIs (Months 1-6)

| Metric | Target |
|--------|--------|
| GitHub stars | 1,000 |
| Free users | 5,000 |
| Paid subscribers | 200 |
| Voices indexed | 12,000+ |
| Average time-to-value | <60 seconds |
| NPS | >50 |

### 12.3 Phase 2 KPIs (Months 6-12)

| Metric | Target |
|--------|--------|
| Free users | 20,000 |
| Paid subscribers | 1,000 |
| Monthly comparisons | 50,000 |
| API integrations | 5 platforms |
| SEO: ranking for "TTS voice comparison" | Top 3 |

### 12.4 Phase 3 KPIs (Months 12-24)

| Metric | Target |
|--------|--------|
| Free users | 100,000 |
| Paid subscribers | 5,000 |
| Enterprise customers | 20 |
| ARR | $5M+ |
| Provider partnerships | 5+ |

---

## 13. Roadmap Summary

```
MONTH  1   2   3   4   5   6   7   8   9  10  11  12
       |---|---|---|---|---|---|---|---|---|---|---|---|
       [  Phase 1: Foundation  ]
       |-- Voice catalog ingestion (9 providers, 12K+ voices)
       |-- Metadata enrichment pipeline (LLM + audio analysis)
       |-- Web app: browse, filter, preview, search
       |-- CLI tool (open source, PyPI)
       |-- Recommendation engine
       |-- Pipecat config generator
                       [  Phase 2: Intelligence  ]
                       |-- A/B comparison UI
                       |-- Latency benchmarks (weekly automated)
                       |-- Cost calculator
                       |-- Community ratings
                       |-- Semantic search ("warm female healthcare voice")
                       |-- Pro tier launch ($29/mo)
                                       [  Phase 3: Platform  ]
                                       |-- Embeddable API
                                       |-- Pipecat plugin
                                       |-- Enterprise tier
                                       |-- Voice branding tools
                                       |-- A/B testing at scale
```

---

## 14. Immediate Next Steps (Week 1-2)

1. **Validate demand**: Landing page + HN/Twitter post. Target 500 email signups.
2. **Build ingestion pipeline**: Start with ElevenLabs shared voices API (11,300+ voices, richest metadata, no auth required).
3. **Enrich the current CLI prototype**: Connect to live provider APIs instead of static catalog.
4. **Set up affiliate programs**: ElevenLabs and Cartesia both have partner programs. Early revenue.
5. **Write first benchmark post**: "TTS Latency & Quality Benchmark Q2 2026" — establishes authority immediately.

---

## Appendix: Research Documents

The following detailed research documents were generated by the analysis team:

- `MARKET_ANALYSIS.md` — TAM/SAM/SOM with sourced data points
- `BUSINESS_STRATEGY.md` — 8 business models analyzed, unit economics, pricing benchmarks
- `PERSONAS_AND_JTBD.md` — 14 personas, pain points, willingness to pay
- `ARCHITECTURE.md` — Full technical architecture, provider API research, database schema
- Competitive landscape report (inline above, sourced from 50+ web fetches)
- Voice agent industry report (inline above, platform metrics and funding data)
