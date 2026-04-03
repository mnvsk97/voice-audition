# TTS Provider Voice Taxonomies

How major providers categorize and describe their voices.

## Cross-Provider Synthesis

### Universal Attributes (all/most providers)
| Attribute | Typical Values |
|-----------|---------------|
| Gender | male, female (some: gender-neutral) |
| Age | youth, adult, middle-aged, elderly |
| Language | ISO codes |
| Accent | american, british, australian + regional |
| Use case/style | narration, conversational, advertising, etc. |
| Speed/tempo | slow, normal, fast (or numeric) |
| Emotion | happy, sad, angry, fearful, surprised, etc. |
| Preview sample | Audio URL |

### Unique Differentiators
| Attribute | Provider | Values |
|-----------|----------|--------|
| Texture | PlayHT | gravelly, smooth, round, thick |
| Loudness (as trait) | PlayHT | whisper, low, neutral, high |
| Descriptive tags | ElevenLabs | Free-form: "wise", "rough", "professional" |
| Stability | ElevenLabs | 0-1 scale for emotional consistency |
| 30+ speaking styles | Azure | customerservice, newscast, empathetic, etc. |
| Style degree | Azure | 0.01-2.0 intensity scale |
| 50+ emotions | Cartesia | neutral thru nostalgic, sarcastic, mysterious |

## Provider Details

### PlayHT (richest structured taxonomy)
- gender: male, female
- age: youth, adult, old
- accent: american, british, australian, canadian
- loudness: whisper, low, neutral, high
- tempo: slow, neutral, fast
- texture: gravelly, smooth, round, thick
- style: narrative, videos, training, advertising, meditation
- emotion (runtime): 12 values (gendered happy/sad/angry/fearful/disgust/surprised)
- voice_guidance: 1-6 (uniqueness), style_guidance: 1-30 (intensity), text_guidance: 1-2

### ElevenLabs (most flexible — prompt-based design)
- gender, age (young/middle_aged/old), accent, language, use_cases, descriptives
- Voice Design supports: gender, age, tone/timbre (deep/warm/gravelly/smooth/raspy/etc.),
  pitch, accent, pacing, emotion, audio quality — all via text prompt
- stability (0-1), similarity_boost (0-1), style (0-1), speed (0-2)

### Azure Speech Service (most speaking styles)
- 30+ styles: cheerful, sad, angry, excited, empathetic, friendly, hopeful, customerservice,
  newscast, narration-professional, chat, assistant, calm, documentary-narration, etc.
- Role play: Girl, Boy, YoungAdultFemale/Male, OlderAdultFemale/Male, SeniorFemale/Male
- Style degree: 0.01-2.0
- Prosody: pitch, rate, volume, contour, emphasis

### Cartesia
- 50+ emotion controls (neutral thru nostalgic, sarcastic, mysterious)
- Speed 0.6x-1.5x, Volume 0.5x-2.0x
- Use-case categories: Support, Gaming, Healthcare, Sales, Voice Agents, Recruiting, etc.

### WellSaid Labs
- Voice style: Promotional, Narration, Conversational
- Smart suggestions by tone, use case, region

### Bland.ai (minimal — phone agent focused)
- 6 preset voices (Josh, Florian, Derek, June, Nat, Paige)
- No descriptive taxonomy exposed

### Speechify
- 13 emotional tones, pitch/speed controls, 60+ languages
- Per-voice use-case tags: "Ads, E-Learning", "Audiobooks, Documentary"
