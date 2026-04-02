# Voice Selection Platform: Business Model & Monetization Strategy

## Comprehensive Analysis — April 2026

---

## 1. MARKET CONTEXT

### The Problem
There are 15+ TTS providers in the market (ElevenLabs, Cartesia, Deepgram, Amazon Polly, Google Cloud TTS, Azure, OpenAI, PlayHT, Murf, WellSaid, Resemble, LMNT, Speechify, Coqui, Fish Audio), each with different:
- Voice catalogs (50 to 1000+ voices)
- Pricing models (per-character, per-minute, per-request)
- Quality characteristics (latency, naturalness, emotion range)
- API interfaces and SDKs
- Language/accent coverage

No single tool lets you **discover, compare, test, and select** the right voice across all providers. Developers and product teams spend hours/days manually evaluating voices.

### Market Size Estimation
- Global TTS market: ~$5-7B (2025), projected $15-20B by 2030 (25-30% CAGR)
- Voice AI agent market: ~$2-3B (2025), projected $12B+ by 2030
- Developer tooling market (API management, testing): ~$8B (2025)
- Addressable market for voice selection tooling: $200M-$500M (1-3% of combined TTS + voice agent spend)

### Who Needs This
| Segment | Size | Pain Level | Willingness to Pay |
|---------|------|------------|-------------------|
| Voice agent developers | 50K-100K globally | HIGH | Medium ($50-200/mo) |
| AI agencies/studios | 5K-10K | HIGH | High ($200-1000/mo) |
| Contact center platforms | 500-1K | VERY HIGH | Very High ($1K-10K/mo) |
| Content creators (podcasts, audiobooks) | 500K+ | Medium | Low ($10-30/mo) |
| Enterprise brand teams | 10K+ | Medium-High | High ($500-5K/mo) |
| TTS providers themselves | 15-30 | Medium | Partnership/rev-share |

---

## 2. BUSINESS MODEL ANALYSIS

### Model A: Freemium SaaS

**How it works:** Free tier for browsing/previewing voices. Paid tiers for advanced comparison, recommendation engine, batch testing, API access, and analytics.

**Proposed Pricing:**

| Tier | Price | Includes |
|------|-------|----------|
| Free | $0 | Browse all voices, 20 previews/day, basic filters |
| Pro | $29/mo | Unlimited previews, side-by-side comparison, voice recommendations, export reports, 500 API calls/mo |
| Team | $79/mo (3 seats) | Everything in Pro + shared voice libraries, team collaboration, 5K API calls/mo, priority support |
| Enterprise | $299-999/mo | Custom voice scoring, brand voice guidelines, SSO, unlimited API, dedicated support |

**Analysis:**
- Revenue potential: Medium-High. At 10K paid users avg $50/mo = $6M ARR
- Scalability: HIGH — software scales, marginal cost per user is low
- Moat: Data moat (voice quality ratings, user preferences, usage patterns)
- CAC: $30-80 (developer tools, content marketing driven)
- Time to revenue: 3-6 months (can charge from day 1 with Pro tier)
- Risks: Free tier may be "good enough" for most users; conversion rate typically 2-5%
- Comparable: Postman ($0 / $9 / $19 / $49 per user/mo), Algolia ($0 / usage-based)

**Verdict: PRIMARY MODEL — Start here.**

---

### Model B: Marketplace / Referral Commission

**How it works:** When users select a voice and sign up for a TTS provider through the platform, earn a referral commission or revenue share.

**Economics:**
- TTS provider monthly spend per customer: $50-500/mo (developer), $1K-10K/mo (enterprise)
- Typical SaaS affiliate commission: 15-30% of first year, or 10-20% recurring
- If referring 500 customers/mo at avg $100/mo spend, 20% commission = $10K/mo recurring
- At scale (5,000 referrals active): $100K/mo = $1.2M ARR from referrals alone

**Analysis:**
- Revenue potential: Medium (supplements SaaS, not standalone)
- Scalability: HIGH — zero marginal cost per referral
- Moat: LOW — any comparison site could do this
- CAC: Same as SaaS (users come for comparison, referrals are a byproduct)
- Time to revenue: 1-3 months (affiliate programs exist today)
- Risks: TTS providers may not want to pay commissions; some have no affiliate programs

**Real-world reference:**
- RapidAPI takes ~20% commission from API providers on their marketplace
- G2/Capterra charge $500-5,000/mo per vendor for lead generation
- AWS Marketplace takes 3-5% on listed software

**Verdict: LAYER THIS ON TOP of the SaaS model. Easy incremental revenue.**

---

### Model C: API-as-a-Service (Embedded Voice Recommendation)

**How it works:** Offer a REST API that other platforms embed to provide voice selection within their products. Voice agent platforms, CMS tools, and contact center software integrate the API.

**Proposed Pricing:**
| Tier | Price | Includes |
|------|-------|----------|
| Free | $0 | 1K API calls/mo |
| Growth | $99/mo | 50K API calls/mo ($0.002/call overage) |
| Scale | $499/mo | 500K API calls/mo ($0.001/call overage) |
| Enterprise | Custom | Unlimited, SLA, dedicated infrastructure |

**Analysis:**
- Revenue potential: HIGH — B2B API businesses can scale massively
- Scalability: VERY HIGH — pure API, usage-based growth
- Moat: HIGH — once embedded, switching costs are significant (API integration stickiness)
- CAC: $500-2,000 (B2B sales, longer cycle)
- Time to revenue: 6-12 months (need to build API, get integrations, prove value)
- Risks: Requires excellent API quality; platforms may build their own

**Real-world reference:**
- Algolia: $0.50-$1.75 per 1K search requests — we could price voice recommendations similarly
- Twilio: $0.0085-0.014/min for voice — pure usage-based, massive scale
- Stripe: 2.9% + $0.30 per transaction — became infrastructure

**Verdict: HIGH-VALUE LONG-TERM PLAY. Build after proving product-market fit with SaaS.**

---

### Model D: Agency/Consulting (Voice Selection as a Service)

**How it works:** Offer hands-on voice selection and optimization as a done-for-you service for enterprises launching voice products.

**Proposed Pricing:**
- Voice audit & recommendation report: $2,500-5,000 (one-time)
- Voice branding package (selection + custom voice development guidance): $10K-25K
- Ongoing voice optimization retainer: $2K-5K/mo

**Analysis:**
- Revenue potential: Medium (capped by human hours)
- Scalability: LOW — requires humans
- Moat: Medium (expertise + proprietary tooling)
- CAC: $200-500 (outbound to voice agent companies)
- Time to revenue: IMMEDIATE (can sell today with the platform as a tool)
- Risks: Doesn't scale; distracts from product development

**Verdict: USE FOR EARLY REVENUE and customer discovery. Phase out as SaaS matures.**

---

### Model E: Enterprise Voice Branding Platform

**How it works:** Help enterprises define, manage, and enforce their "voice brand" across all channels — IVR, voice agents, content, apps. Think "brand guidelines" but for voice.

**Proposed Pricing:**
- Platform fee: $500-2,000/mo base
- Per-voice-asset management: $50-200/mo per voice profile
- Brand voice auditing: $1K-5K per audit
- Multi-channel voice consistency monitoring: $500-2K/mo

**Analysis:**
- Revenue potential: VERY HIGH — enterprise contracts $10K-50K+ ARR each
- Scalability: Medium-High (software + some services)
- Moat: HIGH — deep integration into brand workflows
- CAC: $2,000-10,000 (enterprise sales cycle)
- Time to revenue: 9-18 months (enterprise sales are slow)
- Risks: Long sales cycles; need credibility; market may not be mature yet

**Real-world reference:**
- Veritone (voice marketplace/management): Public company, $150M+ revenue
- Brand management tools (Frontify, Bynder): $500-5,000/mo, $50M+ ARR

**Verdict: PREMIUM EXPANSION after establishing developer base. Huge revenue per customer.**

---

### Model F: Open Source + Hosted Premium

**How it works:** Open source the voice browsing/comparison CLI and core library. Monetize through hosted platform, team features, and managed API.

**Proposed Structure:**
- Open source: CLI tool, voice browser, basic comparison (MIT license)
- Hosted free: Limited usage (same as SaaS free tier)
- Hosted paid: $29-299/mo (same as SaaS tiers)
- Self-hosted enterprise: $999-4,999/yr license

**Analysis:**
- Revenue potential: Medium-High (slower to monetize, but wider adoption)
- Scalability: VERY HIGH (community contributes, reduces development cost)
- Moat: HIGH — community, ecosystem, integrations built by others
- CAC: Very low ($5-20, organic/community driven)
- Time to revenue: 6-12 months (need adoption before conversion)
- Risks: Hard to monetize open source; competitors fork

**Real-world reference:**
- PostHog: Open source analytics, $100M+ valuation, $29-799/mo hosted
- Supabase: Open source Firebase alternative, $25-599/mo, $2B valuation
- GitLab: Open core model, $500M+ ARR

**Verdict: STRONGEST MOAT-BUILDING STRATEGY. Best for developer adoption and long-term defensibility.**

---

### Model G: Data & Insights Business

**How it works:** Aggregate voice quality data, usage trends, provider benchmarks, and sell insights to TTS providers and enterprises.

**Revenue streams:**
- Provider analytics dashboard: $500-2K/mo per provider
- Market intelligence reports: $5K-25K per report
- Voice quality benchmark API: $199-999/mo
- Trend data feeds: $1K-5K/mo

**Analysis:**
- Revenue potential: Medium (niche audience)
- Scalability: HIGH (data sells infinitely)
- Moat: VERY HIGH (proprietary benchmark data)
- CAC: $500-2,000 (B2B sales to providers)
- Time to revenue: 12-18 months (need scale for meaningful data)
- Risks: Need massive usage to generate valuable data; privacy concerns

**Verdict: EXCELLENT SECONDARY REVENUE once you have scale. Don't start here.**

---

## 3. RECOMMENDED BUSINESS MODEL STACK (Phased)

### Phase 1: Months 1-6 — Foundation
**Primary: Open Source + Freemium SaaS**
- Open source the CLI and core comparison engine
- Launch hosted platform with Free + Pro ($29/mo) tiers
- Layer affiliate/referral revenue from TTS providers
- Offer consulting ($2.5K-5K) to fund development and learn the market

**Target:** 5K free users, 200 paid users, $10K/mo revenue
**Total potential:** $6K SaaS + $2K referrals + $5K consulting = $13K/mo

### Phase 2: Months 6-18 — Growth
**Add: Team tier + API-as-a-Service**
- Launch Team ($79/mo) and initial Enterprise tier ($299/mo)
- Ship embeddable API for voice agent platforms
- Build partnership program with TTS providers
- Community-driven voice ratings and reviews

**Target:** 20K free users, 1K paid users, 50 API customers
**Total potential:** $50K SaaS + $25K API + $10K referrals + $10K consulting = $95K/mo

### Phase 3: Months 18-36 — Scale
**Add: Enterprise Voice Branding + Data Business**
- Enterprise platform ($500-5K/mo)
- Voice brand management tools
- Provider analytics and market intelligence
- Custom voice matching/recommendation engine

**Target:** 100K free users, 5K paid users, 200 API customers, 20 enterprise
**Total potential:** $250K SaaS + $100K API + $100K Enterprise + $30K data + $20K referrals = $500K/mo = $6M ARR

---

## 4. PRICING BENCHMARKS FROM COMPARABLE TOOLS

### Developer Tool Pricing Patterns

| Company | Free | Tier 1 | Tier 2 | Enterprise | Model |
|---------|------|--------|--------|------------|-------|
| Postman | $0 | $9/user/mo | $19/user/mo | $49/user/mo | Per-seat |
| Algolia | 10K req/mo free | $0.50/1K req | $1.75/1K req | Custom | Usage-based |
| Twilio | Trial credits | $0.0085/min | Volume discounts | Custom | Pay-as-you-go |
| LiveKit | 1K min free | $50/mo (5K min) | $500/mo (50K min) | Custom | Hybrid |
| Retell AI | $10 credit | $0.07-0.31/min | Volume discounts | Custom | Usage-based |
| Cartesia | 20K credits free | $4/mo | $39/mo | $239/mo+ | Credits |
| Deepgram TTS | $200 credit | $0.030/1K chars | $0.027/1K chars | Custom | Usage-based |

### Key Pricing Insights
1. **Free tiers are mandatory** — every successful dev tool offers one
2. **Usage-based pricing wins** for API products (Twilio, Stripe, Algolia)
3. **Per-seat pricing works** for collaboration tools (Postman, GitHub)
4. **Hybrid models** (base + usage) capture both predictable and variable revenue
5. **The $29/mo sweet spot** — most individual developer tools land here (Speechify Premium is $29/mo, many SaaS tools)
6. **Enterprise multiplier is 10-50x** the individual plan price

### What Developers Will Pay
- Individual developer: $0-29/mo for tooling (price-sensitive)
- Startup team (5-20 people): $79-299/mo (value ROI of time saved)
- Mid-market company: $500-2K/mo (budget exists, needs justification)
- Enterprise: $5K-50K/mo (procurement process, but large budgets)

### The Time-Saved Argument
- A developer spending 2 days evaluating TTS voices = $1,500-3,000 in salary cost
- If the platform saves this to 2 hours, that's $1,200-2,700 saved per evaluation
- ROI is clear even at $29/mo — one evaluation/quarter justifies the cost
- For agencies doing this monthly for clients: 10x the savings

---

## 5. UNIT ECONOMICS

### Cost Structure

**Fixed Costs (Monthly):**
| Item | Cost |
|------|------|
| Cloud infrastructure (API servers, DB) | $200-500 |
| Domain, DNS, CDN | $50 |
| Monitoring/logging (Datadog, etc.) | $100 |
| Auth/identity (Clerk, Auth0) | $0-100 |
| Team salaries (2-person founding team) | $0 (founders) |
| **Total Fixed** | **$350-750/mo** |

**Variable Costs (Per User Action):**
| Action | Provider Cost | Our Markup |
|--------|--------------|------------|
| Voice preview (TTS API call, ~100 chars) | $0.001-0.004 | Free (subsidize at free tier) |
| Side-by-side comparison (2 TTS calls) | $0.002-0.008 | Included in paid tier |
| Batch voice test (50 voices x 200 chars) | $0.05-0.20 | Part of Pro feature |
| Voice recommendation (compute + ML) | $0.001-0.005 | Included in paid tier |

**Cost Per Free User (Monthly):**
- 20 previews/day x 30 days = 600 previews
- Cost: 600 x $0.003 avg = $1.80/mo per active free user
- With 80% of free users being low-activity: ~$0.50/mo avg per free user

**Cost Per Paid User (Monthly):**
- Higher usage: ~$3-8/mo in TTS API costs per paid user
- At $29/mo price point: **73-90% gross margin**
- At $79/mo team price: **90-96% gross margin**

### Margin Analysis

| Tier | Revenue/User | COGS/User | Gross Margin |
|------|-------------|-----------|--------------|
| Free | $0 | $0.50 | -100% |
| Pro ($29) | $29 | $5 | 83% |
| Team ($79) | $79 | $8 | 90% |
| Enterprise ($299) | $299 | $15 | 95% |
| API ($99) | $99 | $10 | 90% |

### Path to Profitability

**Break-even calculation (founder salaries excluded):**
- Fixed costs: $750/mo
- Free user cost: $0.50 x 1,000 active free users = $500/mo
- Total monthly burn: $1,250
- Revenue needed: $1,250 / 0.85 (margin) = ~$1,470/mo
- That's just **51 Pro subscribers** or **19 Team subscribers**

**With founder salaries ($10K/mo each, 2 founders):**
- Total monthly burn: $21,250
- Revenue needed: $21,250 / 0.85 = ~$25,000/mo
- That's **862 Pro subscribers** or **316 Team subscribers**
- Realistically achievable at 10K-15K free users with 5-7% conversion

---

## 6. PARTNERSHIP OPPORTUNITIES

### A. TTS Providers

| Provider | Partnership Type | Value to Them | Value to Us |
|----------|-----------------|---------------|-------------|
| ElevenLabs | Featured listing + affiliate | New customer acquisition channel | Revenue share, $50-200 per referral |
| Cartesia | API partner + co-marketing | Exposure to voice agent developers | Reduced API costs, co-marketing |
| Deepgram | Integration partner | Discovery for their TTS (less known) | Free/reduced TTS API access |
| Amazon Polly | AWS Marketplace listing | Incremental usage | AWS credits, marketplace exposure |
| Google Cloud TTS | GCP partner | Incremental usage | GCP credits |
| PlayHT | Featured listing + affiliate | Customer acquisition | Revenue share |
| Fish Audio | Launch partner | Visibility (newer provider) | Free API access, unique voice catalog |

**Approach:** Position as a **customer acquisition channel** for providers. "We send you qualified, high-intent customers who've already compared voices and chosen yours."

**Revenue model:**
- $500-2K/mo for featured/promoted listings
- 15-25% affiliate commission on referred customers
- Sponsored "recommended voice" placements

### B. Voice Agent Platforms

| Platform | Partnership Type | Value Exchange |
|----------|-----------------|----------------|
| Pipecat | SDK integration | Embed voice selector in Pipecat setup flow |
| LiveKit | Agents marketplace | Voice selection widget for LiveKit Agents |
| Vapi | Embedded API | Voice recommendation in Vapi dashboard |
| Retell AI | Integration | Voice comparison in their builder |
| Bland AI | Embedded API | Voice selection for phone agents |

**Revenue model:** API licensing ($99-499/mo per integration partner) + incremental user growth

### C. AI Agencies

| Opportunity | Details |
|-------------|---------|
| White-label platform | Agencies resell under their brand, $200-500/mo |
| Bulk consulting | Voice selection for their clients, $2K-5K per project |
| Referral program | 20% commission for referring agency clients |

### D. Contact Center Platforms

| Platform | Opportunity |
|----------|------------|
| Five9, Genesys, NICE | Embedded voice selection for IVR/agent voices |
| Talkdesk, Dialpad | Voice recommendation API |
| Amazon Connect | AWS Marketplace integration |

**Revenue:** $1K-10K/mo per enterprise integration

---

## 7. GO-TO-MARKET STRATEGY

### Phase 1: Developer-First (Months 1-6)

**Open Source CLI Launch:**
```
npx voice-suggester compare "Welcome to our service" --providers elevenlabs,cartesia,deepgram
```
- Ship a free, open-source CLI for voice comparison
- Publish to npm, pip — get downloads and GitHub stars
- Goal: 1,000 GitHub stars in 3 months

**Content Marketing Engine:**
- "Best TTS Voices for Contact Centers in 2026" (SEO play)
- "ElevenLabs vs Cartesia vs Deepgram: Voice Quality Benchmark" (comparison content)
- "How to Choose the Right Voice for Your AI Agent" (educational)
- Monthly "Voice Quality Index" benchmark report
- Target keywords: "best tts api", "elevenlabs alternative", "voice comparison", "tts benchmark"

**Community Building:**
- Discord community for voice agent developers
- Voice of the Week / Voice spotlight series
- User-submitted voice reviews and ratings
- Partner with AI Twitter/YouTube creators for reviews

**Developer Relations:**
- Speak at AI/voice conferences
- Publish voice benchmarks (latency, quality scores)
- Contribute to Pipecat, LiveKit ecosystems
- Tutorial content: "Build a Voice Agent with the Perfect Voice in 10 Minutes"

### Phase 2: Product-Led Growth (Months 6-12)

**Viral Mechanics:**
- "Share your voice comparison" — shareable comparison links
- "Powered by VoiceSuggester" badge on voice agent demos
- Embeddable voice preview widget (free)
- Voice selection quiz: "Find your perfect AI voice" (viral content)

**Integration Flywheel:**
- Pipecat plugin: `pip install pipecat-voice-suggester`
- LiveKit integration
- VS Code extension for voice preview while coding
- Zapier/n8n integrations

### Phase 3: Enterprise Expansion (Months 12-24)

- Outbound sales to contact center companies
- Voice branding workshops and webinars
- SOC2 compliance
- Case studies from Phase 1/2 customers
- Channel partnerships with voice agent agencies

---

## 8. COMPETITIVE LANDSCAPE & DEFENSIBILITY

### Potential Competitors

| Competitor | Threat Level | Why |
|------------|-------------|-----|
| TTS providers building their own comparison | Medium | They won't compare against themselves objectively |
| G2/Capterra adding voice comparisons | Low | Too generic, not technical enough |
| A new startup doing the same thing | Medium | First-mover + community + data moat |
| Voice agent platforms adding voice selection | High | They have the user base already |

### Building a Moat

1. **Data moat (STRONGEST):** Every voice comparison generates preference data. Over time, build the world's largest dataset of voice quality preferences, use-case fit, and performance benchmarks. This compounds and is extremely hard to replicate.

2. **Community moat:** Voice reviews, ratings, and recommendations from real users. Like how Stack Overflow's content moat took years to build.

3. **Integration moat:** Once embedded in 10+ voice agent platforms, switching costs are high. Each integration = a mini-moat.

4. **Brand moat:** "The Wirecutter for AI voices" — become the trusted, objective source. Trust takes years to build.

5. **Open source moat:** Community contributions, ecosystem of plugins, and third-party integrations create lock-in without vendor lock-in.

---

## 9. LESSONS FROM SUCCESSFUL DEVELOPER TOOLS

### Postman (Valued at $5.6B)
- **Strategy:** Free tool that solved a universal developer pain point (API testing)
- **Growth:** Bottom-up adoption; developers loved it, brought it to work
- **Monetization:** Took years; focused on team collaboration features as the paid upgrade
- **Lesson for us:** Make the free tool indispensable. Monetize collaboration and team features.

### Stripe (Valued at $65B+)
- **Strategy:** Best-in-class developer experience for payments
- **Growth:** Developer word-of-mouth; "7 lines of code" to accept payments
- **Monetization:** Usage-based from day 1 (2.9% + $0.30 per transaction)
- **Lesson for us:** Developer experience is everything. If the API is beautiful, developers will choose it.

### Algolia (Acquired ~$2B range)
- **Strategy:** Search-as-a-service; developers embed it rather than building their own
- **Growth:** Free tier + usage-based pricing; grows with customer
- **Monetization:** Usage-based ($0.50-1.75 per 1K requests)
- **Lesson for us:** The API/embedded model (Model C) has massive potential. Grow with your customers.

### Twilio ($10B+ revenue)
- **Strategy:** API-first; made telecom accessible to developers
- **Growth:** Pay-as-you-go; no commitment, just start building
- **Monetization:** Usage-based from day 1
- **Lesson for us:** Pay-as-you-go removes barriers. Usage-based = revenue grows with customer success.

### Key Patterns:
1. All started with **developer-first** approach
2. All offered **generous free tiers**
3. All achieved **bottom-up adoption** (developers --> teams --> enterprises)
4. Monetization came from **team/scale features**, not gating the core tool
5. **API stickiness** is the strongest moat — once integrated, rarely replaced
6. **Time to value** was minutes, not days

---

## 10. RISK ANALYSIS

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| TTS providers block API access | Medium | High | Negotiate partnerships; cache voice samples; use official APIs with proper terms |
| Market too small / niche | Low | High | Expand to voice branding, audio content; the voice AI market is growing 25%+ CAGR |
| Big player builds this feature | Medium | Medium | Move fast; build data + community moat; be provider-agnostic (big players won't be) |
| Low conversion from free to paid | Medium | Medium | Focus on enterprise features; ensure free tier is useful but limited; optimize conversion |
| TTS pricing race to bottom reduces value | Low | Medium | Value is in comparison/recommendation, not in TTS itself |
| Voice cloning reduces need for voice selection | Medium | Medium | Pivot to include custom voice comparison/quality scoring |

---

## 11. FINANCIAL PROJECTIONS

### Conservative Scenario (3-Year)

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Free users | 10K | 50K | 150K |
| Paid users | 300 | 2K | 8K |
| Avg revenue/paid user | $40/mo | $55/mo | $70/mo |
| Monthly SaaS revenue | $12K | $110K | $560K |
| API/enterprise revenue | $2K | $40K | $200K |
| Referral/affiliate revenue | $1K | $10K | $30K |
| **Monthly total** | **$15K** | **$160K** | **$790K** |
| **Annual revenue** | **$180K** | **$1.9M** | **$9.5M** |
| Gross margin | 80% | 85% | 88% |
| Team size | 2 | 6 | 15 |

### Optimistic Scenario (Viral adoption + strong partnerships)

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| **Annual revenue** | **$400K** | **$4M** | **$20M** |

---

## 12. IMMEDIATE NEXT STEPS

1. **Validate demand (Week 1-2):**
   - Launch a landing page describing the platform
   - Post on Twitter/LinkedIn/HackerNews: "We're building the Wirecutter for AI voices"
   - Collect email signups; target 500 signups to validate interest

2. **Build MVP (Week 2-6):**
   - Open source CLI: compare voices across 3 providers (ElevenLabs, Cartesia, Deepgram)
   - Hosted web app: browse, filter, preview, compare voices
   - Ship to npm and deploy web app

3. **Early revenue (Week 4-8):**
   - Set up affiliate links with ElevenLabs, Cartesia (they have partner programs)
   - Offer voice consulting to 3-5 early design partners ($2.5K each)
   - Launch Pro tier at $29/mo

4. **Community (Week 6-12):**
   - Discord community
   - First benchmark report: "TTS Latency & Quality Benchmark Q2 2026"
   - Content marketing: 2 comparison articles/week

5. **Partnerships (Week 8-16):**
   - Reach out to TTS providers for API partnerships / reduced rates
   - Propose integration to Pipecat / LiveKit teams
   - Attend/speak at voice AI meetups

---

## SUMMARY: THE RECOMMENDED STRATEGY

**Business model:** Open Source Core + Freemium SaaS + Affiliate Revenue + API-as-a-Service

**Positioning:** "The definitive platform for discovering and selecting AI voices across every provider"

**Pricing sweet spots:** Free / $29/mo / $79/mo / $299+/mo

**Key moats:** Data (voice preferences), Community (reviews/ratings), Integration (embedded in platforms), Brand (trusted benchmark source)

**Year 1 target:** $180K ARR, 10K users, 3 TTS provider partnerships

**Year 3 target:** $9.5M ARR, 150K users, category leader

**The big insight:** The real value isn't in playing audio samples — it's in the **recommendation engine** powered by aggregated preference data. Every comparison makes the platform smarter. This is a data flywheel business disguised as a developer tool.
