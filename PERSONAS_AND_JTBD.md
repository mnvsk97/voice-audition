# Voice Selection Platform: User Personas & Jobs-to-be-Done

## Research Methodology

This document synthesizes findings from:
- Hacker News developer discussions on TTS provider selection
- ElevenLabs, Cartesia, Deepgram, Google Cloud TTS documentation analysis
- Voice AI agent developer communities (Pipecat, Vapi, LiveKit ecosystems)
- Content creator and game developer forums
- E-learning and accessibility practitioner discussions

---

## Part 1: Market Context — The Voice Selection Problem

### The Core Problem Statement

There are now 15+ serious TTS providers (ElevenLabs, Cartesia, Deepgram, Play.ht, Rime, Azure, Google, Amazon Polly, OpenAI, LMNT, WellSaid Labs, Resemble.ai, Coqui/XTTS, Piper, Fish Speech), each offering 10-1000+ voices. A developer building a voice AI agent faces browsing through potentially thousands of voices across multiple provider dashboards, with no standardized way to compare them on the dimensions that actually matter: latency, naturalness, emotional range, cost, language support, and brand fit.

### What People Search For (Search Intent Analysis)

Based on community research, the most common questions when selecting a voice:

1. **"Which TTS provider has the most natural-sounding voices?"** — Quality-first buyers
2. **"What's the fastest TTS for real-time voice agents?"** — Latency-first builders
3. **"ElevenLabs vs Cartesia vs Deepgram for voice AI"** — Comparison shoppers
4. **"Best voice for customer service AI agent"** — Use-case-specific seekers
5. **"Cheapest TTS API with good quality"** — Cost-constrained builders
6. **"How to choose a TTS voice that matches my brand"** — Brand-conscious decision makers
7. **"TTS voices that don't sound robotic"** — Quality threshold seekers
8. **"Best multilingual TTS voice"** — International deployment teams
9. **"TTS voice for healthcare/finance compliance"** — Regulated industry buyers
10. **"Open source TTS voices vs commercial"** — Build-vs-buy evaluators

### Recurring Pain Points from Community Research

| Pain Point | Source | Frequency |
|---|---|---|
| No cross-provider voice comparison tool exists | HN, developer forums | Very High |
| Each provider's voice library has different UX, naming, and metadata | Developer experience | Very High |
| Latency numbers aren't published or comparable across providers | HN developer comments | High |
| Cost structures vary wildly (per-char, per-second, per-request) | HN cost discussions | High |
| Voice sounds great in demo but terrible in production context | Developer complaints | High |
| No way to A/B test voices on YOUR specific scripts/use cases | Developer workflows | High |
| "Uncanny valley" — voices sound good at first but become galling over time | HN audiobook/podcast threads | Medium |
| Emotional range is hard to evaluate from a single demo clip | Developer, CX leader feedback | Medium |
| Subscription fatigue — trialing multiple providers is expensive | E-learning/indie developer threads | Medium |
| Voice quality varies dramatically by language within same provider | Multilingual deployment teams | Medium |

---

## Part 2: Primary Personas (Hands-On Users)

---

### Persona 1: The Voice AI Developer

**Name Archetype:** "Dev Darshan" — Senior software engineer building voice agents

**Demographics & Role:**
- Age: 25-40
- Role: Software engineer, ML engineer, or full-stack developer
- Company: Startup (5-50 people) or mid-size tech company
- Frameworks: Pipecat, LiveKit Agents, Vapi, Retell, Bland.ai, custom WebRTC stacks
- Technical depth: High — comfortable with APIs, SDKs, WebSocket protocols

**Current Workflow (How They Solve This Today):**
1. Read blog posts and HN threads comparing providers
2. Sign up for 3-5 TTS provider free tiers
3. Manually test voices by copying the same text into each provider's playground
4. Listen on laptop speakers (not representative of phone/speaker quality)
5. Pick a voice based on gut feeling after 30-60 minutes of browsing
6. Discover in production that latency, cost, or quality doesn't match expectations
7. Repeat the process when switching providers

**Pain Points:**
- **Time waste**: Spends 2-8 hours across multiple dashboards evaluating voices for each new project
- **No latency data**: Provider dashboards show voice quality but not TTFB (time to first byte) or streaming performance
- **Context mismatch**: Demo text ("The quick brown fox...") doesn't represent their use case (appointment scheduling, customer support, etc.)
- **Provider lock-in fear**: Choosing a voice on one provider means architecture depends on that provider
- **No programmatic comparison**: Can't script voice evaluation — it's all manual clicking and listening
- **Cost modeling is impossible**: Per-character vs per-second vs per-request pricing makes apples-to-apples cost comparison extremely difficult

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Find a voice that sounds natural for my specific use case within 15 minutes, not 4 hours |
| Functional | Compare TTFB/streaming latency across providers with real benchmarks |
| Functional | Test the same script across multiple providers' voices side-by-side |
| Functional | Model cost per minute of conversation across providers |
| Functional | Filter voices by latency budget (e.g., "show me only voices with <300ms TTFB") |
| Emotional | Feel confident I picked the best voice, not just the first acceptable one |
| Emotional | Avoid the anxiety of provider lock-in |
| Social | Recommend the right voice to my team/client with data backing the decision |

**Willingness to Pay:** $29-99/month for a tool that saves 4+ hours per project. Would pay more for API access to programmatic voice comparison.

**Where They Hang Out:**
- Hacker News
- Discord servers: Pipecat, LiveKit, Vapi, ElevenLabs
- GitHub discussions
- r/MachineLearning, r/artificial, r/LocalLLaMA
- Twitter/X (AI engineering community)
- Dev.to, Medium (AI/ML publications)

**What Would Make Them Switch:**
- Side-by-side audio comparison with their own scripts
- Real latency benchmarks (not marketing claims)
- One-click voice migration path between providers
- API for programmatic voice evaluation in CI/CD

---

### Persona 2: The AI Agency Founder/Engineer

**Name Archetype:** "Agency Anika" — Founder of a voice AI development agency

**Demographics & Role:**
- Age: 28-45
- Role: Agency owner, technical co-founder, or lead engineer at a boutique AI dev shop
- Company: 2-15 person agency building voice agents for multiple clients
- Builds: 5-20+ voice agents per year for different clients in different industries
- Revenue model: Project-based ($10K-100K per voice agent deployment)

**Current Workflow:**
1. Client says "we want a voice that sounds professional and warm"
2. Agency manually curates 5-10 voice samples from 2-3 providers
3. Sends audio files to client via email or Slack
4. Client picks one based on subjective preference
5. Agency discovers in integration that the chosen voice has latency or cost issues
6. Awkward conversation with client about switching voices

**Pain Points:**
- **Repeated work**: Does the same voice curation dance for every single client
- **Client communication**: No professional way to present voice options to non-technical clients
- **Multi-industry variety**: Healthcare client needs different voice attributes than a restaurant booking agent
- **Cost pass-through complexity**: Hard to estimate voice costs to build into client quotes
- **Voice consistency across agents**: When building multiple agents for same client, need voices that feel cohesive
- **60-70% platform fees** (cited in HN): Managed platforms like Vapi charge huge markups; need to evaluate raw TTS economics

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Create a shareable voice shortlist for clients in under 30 minutes |
| Functional | Generate professional voice comparison presentations/demos for client reviews |
| Functional | Maintain a curated voice library organized by industry/use case/client |
| Functional | Accurately estimate per-minute voice costs across providers for client proposals |
| Functional | Quickly find voices that match client brand guidelines (tone, age, gender, accent) |
| Emotional | Look professional and knowledgeable when presenting voice options |
| Emotional | Avoid client disappointment when a voice doesn't work in production |
| Social | Differentiate my agency by offering data-driven voice selection (vs. competitors guessing) |

**Willingness to Pay:** $99-299/month (business expense, directly tied to revenue). Would pay per-project pricing for client-facing presentation features. High willingness for white-label options.

**Where They Hang Out:**
- Twitter/X (AI agency community)
- LinkedIn (B2B networking)
- Indie Hackers
- Private Slack/Discord communities for AI agencies
- Y Combinator community (if funded)
- AI meetups and conferences

**What Would Make Them Switch:**
- Client-facing voice comparison links (shareable, branded)
- Industry-specific voice recommendations
- White-label capability
- Cost modeling built into voice selection
- Integration with Pipecat/LiveKit/Vapi for one-click deployment

---

### Persona 3: The Product Manager at a Voice AI Company

**Name Archetype:** "PM Priya" — Product Manager at a company deploying voice agents

**Demographics & Role:**
- Age: 30-45
- Role: Product Manager, Technical Product Manager
- Company: Series A-C startup or enterprise division deploying voice AI
- Context: Company already has voice agents in production; optimizing voice selection
- Stakeholders: Engineering, design, brand, legal, CX leadership

**Current Workflow:**
1. Collects requirements from brand team ("warm, trustworthy, not too young")
2. Asks engineering team to pull voice samples from current provider
3. Runs internal review meeting with 8 people and subjective opinions
4. Conducts ad-hoc user testing with customers (if at all)
5. Decision takes 2-4 weeks due to stakeholder alignment
6. No data on whether the chosen voice actually impacts user satisfaction or completion rates

**Pain Points:**
- **Stakeholder alignment is painful**: Everyone has opinions on voice; no objective framework
- **No metrics**: Can't measure voice quality impact on business outcomes
- **Cross-functional communication**: Brand team speaks different language than engineering team
- **Vendor evaluation**: Boss asks "should we switch from ElevenLabs to Cartesia?" — no way to answer objectively
- **Localization**: Expanding to new markets means re-evaluating voices for every language
- **Compliance gaps**: Legal asks "does this voice meet accessibility requirements?" — no framework to answer

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Create an objective voice evaluation framework stakeholders can align on |
| Functional | Compare current voice against alternatives with quantitative metrics |
| Functional | Run structured voice evaluations across team without 4 meetings |
| Functional | Evaluate voices for new language/market expansion |
| Functional | Document voice selection rationale for compliance and audit purposes |
| Emotional | Feel confident presenting voice recommendations to executives |
| Emotional | Reduce the stress of subjective disagreements in voice selection |
| Social | Be seen as the PM who brings rigor to voice decisions |

**Willingness to Pay:** $199-499/month (team plan). Enterprise plan at $1000+/month for advanced analytics, team collaboration, audit trails.

**Where They Hang Out:**
- LinkedIn
- Product Hunt
- Mind the Product, Lenny's Newsletter
- Internal Slack channels
- Industry conferences (SaaStr, Enterprise Connect)
- Gartner/Forrester reports

**What Would Make Them Switch:**
- Team collaboration features (vote on voices, comment, compare)
- Quantitative voice quality scores (MOS, naturalness, intelligibility)
- A/B testing framework for voices
- Exportable reports for stakeholder reviews
- Compliance checklists

---

### Persona 4: The CX/Contact Center Leader

**Name Archetype:** "CX Carlos" — VP of Customer Experience or Contact Center Director

**Demographics & Role:**
- Age: 35-55
- Role: VP CX, Director of Contact Center Operations, Head of Customer Service
- Company: Mid-market to enterprise (500-10,000+ employees)
- Context: Evaluating or deploying AI voice agents to handle call volume
- KPIs: CSAT, first-call resolution, average handle time, cost per contact

**Current Workflow:**
1. Vendor (Five9, Genesys, NICE, or startup) demos their voice AI solution
2. Vendor picks the voice — CX leader may not even know they have a choice
3. If they do choose, it's from a dropdown of 5-10 voices with generic names
4. No testing with actual customers before deployment
5. Post-deployment: "customers are complaining the voice sounds robotic"

**Pain Points:**
- **Not technical**: Doesn't know what TTS providers exist or how to evaluate them
- **Vendor dependency**: Relies on CCaaS vendor's voice options, which may be limited
- **Customer trust**: Research shows voice quality directly impacts caller trust and satisfaction
- **3-second delays are unacceptable**: Cited in HN as a dealbreaker — "the 3-second delay in commercial voice bots"
- **Brand consistency**: Voice agent should sound like it belongs to the brand
- **Escalation rates**: Bad voice = more "let me speak to a human" requests

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Evaluate whether my current AI voice is optimal for customer satisfaction |
| Functional | Hear how different voices sound handling my actual call scenarios (billing inquiry, appointment scheduling, complaint) |
| Functional | Understand the cost implications of different voice quality tiers |
| Functional | Get a recommendation based on my industry and use case |
| Emotional | Feel confident that customers won't be annoyed by the AI voice |
| Emotional | Avoid being blamed for a bad voice AI deployment |
| Social | Present a modern, professional brand image through voice |

**Willingness to Pay:** $500-2000/month as part of voice AI evaluation budget. Would prefer annual contracts. Influenced by analyst reports (Gartner, Forrester).

**Where They Hang Out:**
- LinkedIn
- ICMI (International Customer Management Institute)
- CCW (Customer Contact Week)
- Gartner Customer Service & Support Summit
- CX Network
- Vendor webinars and demos

**What Would Make Them Switch:**
- Industry benchmarks ("best voices for healthcare contact centers")
- Non-technical interface — no API needed
- Customer satisfaction correlation data
- Easy demo generation for executive buy-in
- Integration with existing CCaaS platforms

---

## Part 3: Secondary Personas (Influencers & Decision-Makers)

---

### Persona 5: The Brand Manager

**Name Archetype:** "Brand Bianca" — Brand strategist ensuring voice AI aligns with brand identity

**Demographics & Role:**
- Age: 28-45
- Role: Brand Manager, Brand Director, Head of Brand
- Company: Consumer brand, financial services, healthcare, retail
- Context: Company is adding AI voice touchpoints; brand team wants consistency

**Pain Points:**
- Voice AI is a new brand touchpoint nobody planned for in brand guidelines
- No vocabulary to describe desired voice qualities technically ("warm but authoritative" means what exactly?)
- Disconnect between brand adjectives and TTS voice parameters
- Fear of brand dilution — "what if our AI sounds like everyone else's AI?"
- No way to evaluate voices against brand personality framework

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Translate brand attributes (trustworthy, innovative, caring) into voice characteristics |
| Functional | Audit current AI voice against brand guidelines |
| Functional | Create a "voice brand guide" that engineering can implement |
| Emotional | Feel ownership over how the brand sounds, not just how it looks |
| Social | Demonstrate brand leadership by proactively defining voice identity |

**Willingness to Pay:** Influences budget but doesn't hold it directly. Would advocate for $200-500/month within broader brand tools budget.

**Where They Hang Out:** LinkedIn, Brandweek, Digiday, internal brand Slack channels, design conferences

---

### Persona 6: The Compliance/Legal Officer

**Name Archetype:** "Compliance Claudia" — Ensuring voice AI meets regulatory requirements

**Demographics & Role:**
- Age: 35-55
- Role: Compliance Officer, Legal Counsel, Risk Manager
- Industries: Healthcare (HIPAA), Finance (FINRA/SEC), Insurance, Government
- Context: Must approve AI voice deployments; needs audit trails

**Pain Points:**
- No framework for evaluating voice AI compliance
- Unclear regulations around AI voice disclosure requirements (must you tell callers it's AI?)
- Accessibility requirements (ADA, WCAG) for voice interactions are ambiguous
- Data residency concerns — where is voice synthesis happening?
- Voice cloning raises consent and IP questions
- Need documentation trail for audit purposes

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Verify that a TTS provider meets data residency and processing requirements |
| Functional | Document voice selection rationale for regulatory audits |
| Functional | Ensure voice agent includes required disclosures (AI transparency laws) |
| Functional | Evaluate provider compliance certifications (SOC 2, HIPAA BAA, etc.) |
| Emotional | Feel confident that voice AI won't create regulatory exposure |

**Willingness to Pay:** Doesn't hold budget but can block purchases. Values compliance documentation features as part of enterprise pricing.

**Where They Hang Out:** Legal/compliance conferences, industry-specific regulatory forums, internal legal channels

---

### Persona 7: The Accessibility Specialist

**Name Archetype:** "Accessibility Alex" — Ensuring voice interfaces work for all users

**Demographics & Role:**
- Age: 30-50
- Role: Accessibility Specialist, Inclusive Design Lead, UX Researcher
- Context: Evaluating voice AI for users with hearing impairments, cognitive disabilities, non-native speakers

**Pain Points:**
- Speech rate, clarity, and pronunciation quality vary wildly across voices
- No accessibility-specific voice evaluation criteria
- Voices optimized for "naturalness" may sacrifice intelligibility
- Non-native speakers may struggle with certain accents
- No standard for how voices perform with hearing aids or assistive devices

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Evaluate voice intelligibility across different listening conditions |
| Functional | Find voices with adjustable speech rate that maintain quality |
| Functional | Test pronunciation accuracy for domain-specific terminology |
| Functional | Assess voice clarity for users with hearing impairments |
| Emotional | Advocate effectively for inclusive voice selection |

**Willingness to Pay:** Part of broader accessibility tooling budget. $50-200/month.

---

### Persona 8: The UX Designer

**Name Archetype:** "UX Uma" — Designing the end-to-end voice experience

**Demographics & Role:**
- Age: 27-40
- Role: UX Designer, Conversation Designer, Voice UX Designer
- Context: Designing voice interactions; voice selection is one piece of the experience

**Pain Points:**
- Voice selection happens after UX design is "done" — should be part of the design process
- No prototyping tools that let you test different voices in conversation flows
- Hard to communicate voice preferences to engineering ("make it sound more empathetic")
- Current tools are developer-oriented, not designer-friendly

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Preview how different voices sound in actual conversation flow prototypes |
| Functional | Create voice mood boards alongside visual mood boards |
| Functional | Test emotional range — same voice doing happy, empathetic, serious, apologetic |
| Emotional | Have a seat at the table in voice selection decisions |
| Social | Bring the same rigor to voice design as visual design |

**Willingness to Pay:** $30-100/month as individual tool. Would advocate for team license.

**Where They Hang Out:** Figma community, Dribbble, UX conferences, Voice UX meetups, LinkedIn

---

## Part 4: Tertiary Personas (Unexpected Users)

---

### Persona 9: The Content Creator / YouTuber

**Name Archetype:** "Creator Chris" — Making videos, shorts, and social content with AI voices

**Demographics & Role:**
- Age: 18-35
- Role: YouTuber, TikToker, social media content creator
- Context: Needs voiceover for videos; doesn't want to use own voice or can't afford voice actors
- Volume: 2-20+ videos per month

**Pain Points:**
- ElevenLabs is the default but expensive at scale (subscription limits)
- Free TTS sounds robotic and hurts engagement
- Finding a distinctive voice that becomes part of their brand
- No easy way to test voices with their actual video scripts
- Subscription fatigue from trialing multiple services

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Find a voice that sounds good enough that viewers don't click away |
| Functional | Compare free/cheap options against premium to know if the upgrade is worth it |
| Functional | Find a unique voice that doesn't sound like every other AI video |
| Emotional | Sound professional without spending professional money |

**Willingness to Pay:** $0-29/month. Very price-sensitive. Ad-supported free tier would drive adoption.

**Where They Hang Out:** YouTube, TikTok, r/YouTubers, r/NewTubers, Twitter/X, creator Discord servers

---

### Persona 10: The Game Developer

**Name Archetype:** "Game Dev Gabe" — Building games with AI-voiced NPCs

**Demographics & Role:**
- Age: 22-40
- Role: Indie game developer or small studio lead
- Context: Needs 10-100+ distinct character voices; can't afford voice actors for all NPCs
- Engine: Unity, Unreal, Godot

**Pain Points (from research):**
- **Consistency**: "There can still be a lot of variance in speech patterns/tone/inflections" even with same parameters
- Need voices that maintain character identity across hundreds of lines of dialogue
- Each NPC needs a distinct personality conveyed through voice
- Real-time TTS for dynamic dialogue vs. pre-rendered for scripted content
- Integration with game engines is non-trivial
- Voice cloning could help but raises ethical/legal questions

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Find 10-50 distinct voices that can represent different NPC archetypes |
| Functional | Ensure voice consistency across long dialogue trees |
| Functional | Preview voices with game-specific scripts (fantasy, sci-fi, modern) |
| Functional | Evaluate real-time TTS latency for dynamic conversation systems |
| Emotional | Create immersive worlds that feel alive through voice variety |

**Willingness to Pay:** $29-99/month during development. Interested in perpetual/bulk licensing for shipped games.

**Where They Hang Out:** r/gamedev, r/indiedev, Unity/Unreal forums, GDC, game dev Discord servers, itch.io

---

### Persona 11: The E-Learning Producer

**Name Archetype:** "E-Learn Elena" — Creating online courses and training content

**Demographics & Role:**
- Age: 30-50
- Role: Instructional Designer, E-Learning Developer, L&D Manager
- Company: EdTech company, corporate training department, university
- Context: Narrating hundreds of hours of educational content

**Pain Points (from research):**
- **Cost**: Professional narrators are expensive; re-recording after content updates is prohibitive
- **Scale**: Hundreds of modules need consistent voice across months of production
- **900+ voice options**: One developer cited needing to evaluate 900+ Piper TTS voices — overwhelming without tools
- **Subscription fatigue and API rate limits** cited as major frustrations
- **Language variety**: Global organizations need consistent quality across 10-30 languages
- Voices optimized for conversation may not work well for educational narration (different prosody needs)

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Find a clear, pleasant narration voice that works for 8+ hours of content |
| Functional | Evaluate voice fatigue — does this voice become annoying after 30 minutes? |
| Functional | Compare voices for pronunciation of technical/domain terminology |
| Functional | Find matching voices across multiple languages for localized courses |
| Emotional | Maintain production quality while significantly reducing costs |

**Willingness to Pay:** $49-199/month. Institutional purchases possible at $500+/year.

**Where They Hang Out:** ATD (Association for Talent Development), eLearning Industry, Articulate community, LinkedIn L&D groups

---

### Persona 12: The Podcast Producer

**Name Archetype:** "Podcast Pat" — Producing AI-narrated or AI-enhanced podcasts

**Demographics & Role:**
- Age: 25-45
- Role: Independent podcast producer or media company producer
- Context: Using AI voices for news roundups, content repurposing, or fully AI-narrated shows

**Pain Points (from research):**
- **Extended listening fatigue**: AI voices that sound "shockingly good" in demos become "galling and distracting" after extended listening
- **Style preservation**: "Whatever it produces doesn't have my 'voice'" — the AI narration doesn't capture the creator's unique style
- **Tone variance**: "Listeners may still be able to tell it's not a human because the tone doesn't have much variance"
- Limited ability to inject personality, humor, and emotional dynamics
- Platform restrictions (some podcast platforms may flag AI-generated content)

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Find a voice that can sustain listener engagement for 20-60 minutes |
| Functional | Test voices with long-form content samples, not just short clips |
| Functional | Evaluate emotional range and dynamic variation over extended narration |
| Emotional | Produce content that listeners enjoy, not merely tolerate |

**Willingness to Pay:** $29-99/month. Would pay more for voices specifically optimized for long-form narration.

---

### Persona 13: The Audiobook Producer

**Name Archetype:** "Audio Amara" — Producing AI-narrated audiobooks

**Demographics & Role:**
- Age: 30-55
- Role: Independent author, audiobook producer, publishing house
- Context: Narrating books that are 5-20+ hours long

**Pain Points (from research):**
- **Quality over marathon listening**: "occasional clip/skip text, prolonged silence, long/warped/garbled words" — small glitches are unacceptable in a 10-hour production
- **Character differentiation**: Need distinct voices for narrators vs. multiple characters
- **Distribution gatekeeping**: "Platforms like Audible only accept human-narrated audiobooks"
- **Uncanny valley at scale**: Initially "shockingly good" but becomes "galling" — extended listening reveals flaws
- Professional narrators provide "consistent and distinct character voices with emotional understanding that current TTS struggles to match"

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Evaluate voice consistency and quality over 10+ hours of narration |
| Functional | Find character voice sets that sound distinct but cohesive |
| Functional | Test pronunciation of names, places, and unusual words |
| Functional | Identify which platforms accept AI-narrated content |
| Emotional | Produce audiobooks I'm proud of, not just cheap alternatives |

**Willingness to Pay:** $49-199/month. Volume-based pricing preferred. Per-book pricing model would be attractive.

---

### Persona 14: The Accessibility Tool Builder

**Name Archetype:** "A11y Ari" — Building tools for visually impaired or reading-disabled users

**Demographics & Role:**
- Age: 28-45
- Role: Developer at assistive technology company or nonprofit
- Context: Building screen readers, reading assistants, or accessibility overlays
- Users: Visually impaired, dyslexic, non-native speakers

**Pain Points (from research):**
- **Subscription costs add up fast** for "anyone who needs TTS regularly (accessibility, content creation, language learning)"
- Need voices that prioritize intelligibility over naturalness
- Must work across diverse content types (web pages, documents, emails)
- Speed adjustment without quality degradation is critical
- Open-source options (Piper, Coqui) have fewer premium voices

**Jobs-to-be-Done:**

| Type | Job |
|---|---|
| Functional | Find voices that maximize intelligibility at various speech rates |
| Functional | Evaluate cost per hour of synthesis for high-volume use cases |
| Functional | Compare open-source vs. commercial voices for accessibility-grade quality |
| Functional | Test voices with diverse content types (technical text, casual text, navigation) |
| Emotional | Provide the best possible experience for users who depend on TTS daily |

**Willingness to Pay:** $29-99/month. Strongly prefer open-source or bulk/nonprofit pricing. Need predictable costs for high-volume usage.

---

## Part 5: Cross-Cutting Decision Criteria

### What Questions Do People Ask When Picking a Voice?

Based on all research, these are the universal questions organized by decision stage:

**Stage 1: Discovery (What's out there?)**
1. Which TTS providers exist and what are their strengths?
2. How many voices does each provider offer?
3. Which providers support my target language(s)?
4. What's the pricing model for each provider?

**Stage 2: Shortlisting (Narrow the field)**
5. Which voices sound most natural for my use case (conversation vs. narration vs. notification)?
6. What's the latency profile? Can it work in real-time?
7. Does the voice have emotional range or is it monotone?
8. What gender, age, accent options are available?
9. Is the voice available via streaming API?
10. What's the cost per minute/character at my expected volume?

**Stage 3: Evaluation (Deep comparison)**
11. How does this voice sound with MY specific scripts/content?
12. Does it maintain quality over extended use (no uncanny valley fatigue)?
13. How does it handle domain-specific terminology, names, abbreviations?
14. What's the voice's performance on different audio devices (phone, speaker, headset)?
15. Can I customize pronunciation, speed, pitch, and emphasis?

**Stage 4: Decision (Final selection)**
16. Does this voice align with our brand personality?
17. Does the provider offer the reliability/uptime we need?
18. What are the compliance/data residency implications?
19. Is there vendor lock-in risk? How hard is it to switch later?
20. What do our end users/customers actually prefer? (A/B test data)

---

## Part 6: Opportunity Sizing by Persona

| Persona | Market Size (est.) | Urgency | Willingness to Pay | Acquisition Channel |
|---|---|---|---|---|
| Voice AI Developer | 50K-200K globally | Very High | $29-99/mo | HN, Twitter/X, Discord, SEO |
| AI Agency Founder | 5K-20K globally | Very High | $99-299/mo | Twitter/X, LinkedIn, referral |
| Product Manager (Voice AI) | 10K-50K globally | High | $199-499/mo | LinkedIn, Product Hunt, SEO |
| CX/Contact Center Leader | 50K-200K globally | High | $500-2000/mo | LinkedIn, analyst reports, events |
| Brand Manager | 100K+ globally | Medium | Influences budget | LinkedIn, conferences |
| Compliance Officer | 50K+ in regulated industries | Medium | Blocks or approves | Industry events |
| Accessibility Specialist | 10K-30K globally | Medium | $50-200/mo | A11y communities |
| UX Designer | 20K-50K globally | Medium | $30-100/mo | Figma community, design events |
| Content Creator | 1M+ globally | Medium | $0-29/mo | YouTube, TikTok, SEO |
| Game Developer | 100K-500K globally | Low-Medium | $29-99/mo | Reddit, game dev forums |
| E-Learning Producer | 50K-200K globally | Medium | $49-199/mo | ATD, eLearning Industry |
| Podcast Producer | 50K-200K globally | Low-Medium | $29-99/mo | Podcast communities |
| Audiobook Producer | 20K-100K globally | Low-Medium | $49-199/mo | Publishing communities |
| Accessibility Tool Builder | 5K-15K globally | Medium | $29-99/mo | A11y conferences, GitHub |

---

## Part 7: Strategic Recommendations

### Who to Build For First (Prioritized)

**Tier 1 — Launch Personas (Month 1-3):**
1. **Voice AI Developer** — Highest urgency, most vocal community, drives word-of-mouth. They will find and champion this tool.
2. **AI Agency Founder** — High willingness to pay, multiplier effect (each agency serves multiple clients). Need client-facing features.

**Tier 2 — Growth Personas (Month 3-6):**
3. **Product Manager at Voice AI Company** — Team features, collaboration, reporting. Drives B2B revenue.
4. **CX/Contact Center Leader** — Highest willingness to pay per seat. Needs non-technical interface. Driven by analyst mentions and case studies.

**Tier 3 — Expansion Personas (Month 6-12):**
5. **Content Creators** — Massive volume, low WTP, but drives SEO and brand awareness. Free tier with conversion funnel.
6. **E-Learning Producers** — Steady, predictable demand. Institutional sales possible.
7. **Game Developers** — Unique use case (many voices needed). Niche but growing with AI NPCs trend.

### Key Feature Mapping to Persona Needs

| Feature | Dev | Agency | PM | CX | Brand | Content | Game | E-Learn |
|---|---|---|---|---|---|---|---|---|
| Cross-provider voice search & filter | P0 | P0 | P0 | P0 | P1 | P1 | P0 | P0 |
| Side-by-side audio comparison | P0 | P0 | P0 | P1 | P1 | P1 | P1 | P1 |
| Custom script testing | P0 | P0 | P1 | P1 | P1 | P0 | P0 | P0 |
| Latency benchmarks | P0 | P0 | P1 | P1 | - | - | P0 | - |
| Cost calculator/modeling | P0 | P0 | P0 | P0 | - | P0 | P1 | P0 |
| Shareable comparison links | P1 | P0 | P0 | P1 | P0 | - | - | - |
| Team collaboration (voting, comments) | - | P1 | P0 | P1 | P1 | - | - | P1 |
| Brand personality matching | - | P1 | P1 | P1 | P0 | P1 | - | - |
| Emotional range previews | P1 | P1 | P1 | P1 | P1 | P1 | P0 | P1 |
| Long-form fatigue testing | - | - | P1 | - | - | P1 | - | P0 |
| Compliance/data residency info | - | P1 | P1 | P1 | - | - | - | - |
| API for programmatic evaluation | P0 | P1 | - | - | - | - | P1 | - |
| Voice set curation (multiple distinct voices) | - | P1 | - | - | - | - | P0 | P1 |

*P0 = Must have, P1 = Important, - = Not critical*

---

## Part 8: Competitive Landscape (How People Solve This Today)

| Current Solution | What It Does | What It Lacks |
|---|---|---|
| ElevenLabs Voice Library | Browse/search ElevenLabs voices only | Single provider, no latency data, no cost comparison |
| Play.ht Voice Library | Browse Play.ht voices | Single provider |
| Provider API playgrounds | Test individual voices | No cross-provider comparison, no custom scripts at scale |
| Manual spreadsheet tracking | Developer creates own comparison | Massive time investment, no audio playback, stale data |
| Blog posts ("Best TTS 2025") | Subjective comparisons | Outdated, not interactive, generic scripts |
| YouTube comparison videos | Audio demos | Not personalized, can't test your own scripts |
| Word of mouth / Discord | Ask community what they use | Anecdotal, biased, incomplete |

**Gap**: No tool exists that lets you search, filter, compare, and evaluate TTS voices across all major providers in one interface with real benchmarks, custom scripts, and collaboration features.

---

*Document generated: April 2026*
*Research sources: HN Algolia API, Google Cloud TTS docs, developer community forums, TTS provider documentation*
