# Voice Schema Research

Research findings that inform the VoiceAudition voice catalog schema design.
Conducted April 2026 using 6 parallel research agents across academic papers,
provider APIs, industry blogs, and psychology studies.

## Research Files

| File | Contents |
|------|----------|
| [voice_perception_psychology.md](voice_perception_psychology.md) | Psychology of voice perception — trust, warmth, authority, gender, accent, uncanny valley |
| [acoustic_parameters.md](acoustic_parameters.md) | eGeMAPS 88-feature set, GRBAS scale, librosa/openSMILE features, Big Five from voice |
| [provider_taxonomies.md](provider_taxonomies.md) | How ElevenLabs, PlayHT, Cartesia, Azure, Google, WellSaid, Speechify, Bland categorize voices |
| [voice_agent_best_practices.md](voice_agent_best_practices.md) | Deepgram emotional voice accuracy tax, Retell/Bland/Vapi best practices, use-case profiles |
| [voice_quality_standards.md](voice_quality_standards.md) | ITU-T P.85, MOS variants, Seebauer 8-dimension model, TTS evaluation metrics |

## Top-Line Findings

### 1. Two Axes of Voice Perception (McAleer et al., PLOS ONE 2014)
All voice personality judgments collapse into two dimensions explaining ~88% of variance:
- **Valence** (trust + warmth + likeability)
- **Dominance** (authority + competence + power)

You cannot maximize both simultaneously.

### 2. Acoustic Features Poorly Predict Personality (Seebauer et al., SSW 2023)
Common acoustic features had "very weak correlations" with perceived voice personality.
A model must LISTEN and describe — acoustic measurements alone are insufficient.

### 3. Speech Rate Is The #1 Trust Predictor
Speech rate (beta = -0.61) beats pitch, HNR, voice quality, speaker age, and gender
as a predictor of perceived trustworthiness. Most voice systems over-index on pitch.

### 4. Emotional Voices: 50% Better CSAT, 20% Worse Accuracy (Deepgram)
- Emotional TTS drops entity recognition 7-20 percentage points
- WER increases 25-35% vs neutral baselines
- But CSAT improves up to 50% in contact centers
- Cost: 4-10x multiplier (up to 40x for premium)

### 5. No Uncanny Valley for Voice (Kuhne et al., 2020)
Unlike faces, more human-like voice = consistently better. The risk is inconsistency
between human-like and robotic features, not excessive naturalness.

### 6. Gender-Neutral = 145-175 Hz
The fundamental frequency range for gender-neutral perception falls between typical
male (~85-155 Hz) and female (~165-255 Hz) ranges.

## Key Sources

| Source | Finding |
|--------|---------|
| McAleer, Todorov & Belin (PLOS ONE, 2014) | 2-axis voice perception model from 391ms "hello" |
| Seebauer et al. (SSW, 2023) | 8 perceptual dimensions; weak acoustic-personality correlations |
| Eyben, Scherer et al. (2016) | eGeMAPS 88-feature standard for computational paralinguistics |
| Deepgram research blog | Emotional voice accuracy/cost tradeoff |
| Kuhne, Fischer & Zhou (Frontiers, 2020) | No uncanny valley in voice |
| Boduch-Grabka & Lev-Ari (2021) | Accent bias reducible via exposure |
| Spielmann & Stern (2026) | Gender-stereotypical AI voice preferences |
| Maltezou-Papastylianou et al. (2025) | Voice acoustics impact trust in humans AND machines |
| Azure Speech Service docs | 30+ speaking styles — richest commercial taxonomy |
| PlayHT API docs | Richest structured voice taxonomy (texture, tempo, loudness) |
