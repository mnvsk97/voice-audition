# VoiceAudition Design System

## Product Context
VoiceAudition is an open source voice casting tool for AI agents. Users describe their project in natural language, and the tool recommends TTS voices from a catalog of 12,000+ voices across 6+ providers. The key interaction is: describe → audition → listen → pick → get config.

## Key Pages
1. **Playground** — the main product page. Text input → AI-powered voice recommendations with audio players → shareable URL
2. **Voice Directory** — browsable catalog of all voices with filters (secondary, linked from playground)

## JTBD
- "I'm building a voice agent and need to find the right voice in minutes, not hours"
- "I want to hear voice options that fit my business context before I commit"
- "I want to share voice options with my team or client"

## Target Users
- Voice AI developers (Pipecat, LiveKit, Vapi)
- AI agency founders building agents for clients
- Technical, value simplicity and speed

## Branding & Visual Direction

### Color Palette (warm, soft, inviting — inspired by Thread Surrogacy aesthetic)
- Background: #FFF5EE (warm peach/seashell)
- Background gradient: linear-gradient(180deg, #FFF5EE 0%, #FFEEE4 50%, #FFF0E8 100%)
- Surface/cards: #FFFFFF (white)
- Surface elevated: #FFF8F4 (slightly warm white)
- Border: #E8D5CC (warm tan border)
- Border subtle: #F0E0D8 (lighter tan)
- Text primary: #1A0A12 (deep near-black with warm undertone)
- Text secondary: #6B5660 (muted warm gray)
- Text muted: #9A8A92 (lighter warm gray)
- Primary/accent: #410028 (deep maroon/burgundy)
- Primary hover: #5A0038 (slightly lighter maroon)
- Primary text: #FFFFFF (white on primary buttons)
- Secondary button bg: #FFFFFF (white with border)
- Secondary button border: #D4C0C8 (muted pink-gray)
- Success: #2D6A4F (muted forest green)
- Warning: #B8860B (dark goldenrod)
- Error: #8B0000 (dark red)
- Provider badges:
  - Cartesia: #1E3A5F bg, #87CEEB text
  - ElevenLabs: #3D1452 bg, #C9A0DC text
  - Deepgram: #1A3A2A bg, #6FCF97 text
  - OpenAI: #2A2A2A bg, #D4D4D4 text
  - PlayHT: #3D1A2A bg, #E8A0B0 text
  - Rime: #1A3A3A bg, #80CBC4 text

### Typography
- Font family: Inter (system fallback: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif)
- Monospace: 'SF Mono', Consolas, monospace (for code snippets, voice IDs, Pipecat configs)
- Page title: 28-32px, weight 600, #1A0A12
- Section headings: 18-20px, weight 600, #1A0A12
- Body: 15-16px, weight 400, #1A0A12, line-height 1.6
- Secondary/descriptions: 14px, weight 400, #6B5660
- Labels/chips: 12px, weight 500, uppercase optional
- Code blocks: 13px, SF Mono, #1A0A12 on #FFF8F4 background

### Spacing
- Base unit: 4px
- Component padding: 16-24px
- Card padding: 20-28px
- Section gaps: 40-56px
- Container max-width: 720px (focused, not wide — conversational feel)
- Border radius: 16px (cards, large containers), 12px (buttons, inputs), 24px (pills/chips), 50% (round play buttons)

### Components
- Cards: white background, 1px #E8D5CC border, 16px radius, subtle shadow (0 1px 3px rgba(65,0,40,0.06)), hover shadow increases
- Primary button: #410028 bg, white text, 12px radius, 48px height, full-width or auto, subtle shadow
- Secondary button: white bg, 1px #D4C0C8 border, #410028 text, 12px radius, 48px height
- Text input/textarea: white bg, 1px #E8D5CC border, 12px radius, 16px padding, placeholder in #9A8A92, focus border #410028
- Example chips: pill-shaped (#FFF8F4 bg, 1px #E8D5CC border, 24px radius), hover bg #FFEEE4
- Play button: 44px circle, #410028 bg, white triangle icon, hover #5A0038
- Provider badges: small rounded chips with provider-specific bg/text colors (see above)
- Trait bars: thin 4px height, #F0E0D8 track, #410028 fill, 60px wide
- Code blocks: #FFF8F4 bg, 1px #E8D5CC border, 12px radius, monospace font

### Layout
- Single column, centered (720px max)
- Light mode only
- Warm, breathing whitespace — generous padding
- Minimal chrome — no heavy nav, no sidebar
- The text input is the hero — large, prominent, inviting
- Cards have soft shadows, not hard borders

### Tone
- Warm and approachable, but still professional
- Clean, not clinical
- Soft edges, rounded corners, breathing room
- Feels like a trusted tool, not a cold developer terminal

### Motion
- Subtle: 200ms ease transitions on hover/focus
- Cards: slight shadow lift on hover
- Buttons: subtle scale(1.01) on hover
- Loading states: gentle pulse animation
