# Voice Quality Standards & Evaluation

## ITU-T P.85 (1994)
"A method for subjective performance assessment of the quality of speech voice output devices"
Standard for evaluating TTS quality. Measures multiple dimensions beyond a single score.

## MOS and Variants
| Metric | Scale | Measures |
|--------|-------|---------|
| MOS (Mean Opinion Score) | 1-5 ordinal | Overall perceived quality |
| CMOS (Comparative MOS) | -3 to +3 relative | Quality comparison between two systems |
| SMOS (Speaker MOS) | 1-5 ordinal | Speaker similarity/identity preservation |
| DMOS (Degradation MOS) | 1-5 ordinal | Degree of quality degradation |
| MUSHRA | 0-100 continuous | Quality with multiple hidden references |

Critique: "Stuck in the MOS pit" (Kirkland et al., SSW 2023) — MOS methodology applied
inconsistently across studies, making cross-study comparison unreliable.

## Seebauer 8-Dimension Model (SSW 2023)
"Re-examining the quality dimensions of synthetic speech" — the most directly relevant
framework for voice agent selection:

| Dimension | Type | Relevance |
|-----------|------|-----------|
| Human-likeness | Continuous | Naturalness (classic MOS target) |
| Audio quality | Continuous | Technical artifacts, distortion |
| Negative emotion | Continuous | Sad, angry, tense |
| Positive emotion | Continuous | Happy, warm, enthusiastic |
| Dominance | Continuous | Assertiveness, authority, confidence |
| Calmness | Continuous | Composure, relaxation, steadiness |
| Seniority | Continuous | Perceived age |
| Gender | Orthogonal | Perceived speaker gender |

**Critical finding:** Common acoustic features had "very weak correlations" with these
subjective scales, and inter-rater agreement was low within scales. Perceived voice
personality is hard to predict from acoustic measurements alone.

## Objective TTS Metrics
| Metric | Measures | Type |
|--------|----------|------|
| WER | Intelligibility | Lower is better |
| MCD (Mel-Cepstral Distortion) | Acoustic distance from reference | Lower is better |
| Sim-O / Sim-R | Speaker similarity | Higher is better |
| PESQ / POLQA | Perceptual quality (ITU) | Continuous |
| F0 RMSE | Pitch accuracy | Lower is better |
| TTSDS | Multi-factor distribution score | Composite |

## TTSDS (TTS Distribution Score)
Evaluates synthetic speech across: Prosody, Speaker identity, Intelligibility.
Benchmarks 35 TTS systems (2008-2024). Strong correlation with human evaluations.

## VAD Model (Valence-Arousal-Dominance)
From IEMOCAP emotional speech database. Standard dimensional framework:
- **Valence**: negative ↔ positive (continuous)
- **Arousal/Activation**: calm ↔ excited (continuous)
- **Dominance**: submissive ↔ dominant (continuous)

Maps directly to voice agent selection:
- Customer service: moderate arousal, positive valence, moderate dominance
- Medical assistant: low arousal, neutral-positive valence, low dominance
- Sales: high arousal, positive valence, moderate dominance

## Emotional Speech Databases

### RAVDESS
- 7,356 files, 24 actors (12F/12M), North American English
- 8 emotions: neutral, calm, happy, sad, angry, fearful, surprise, disgust
- 2 intensity levels: normal, strong
- Validated by 247 participants (10 ratings/file)

### CREMA-D
- 7,442 clips, 91 actors (48M/43F), ages 20-74, diverse ethnicities
- 6 emotions: Anger, Disgust, Fear, Happy, Neutral, Sad
- 4 intensity levels: Low, Medium, High, Unspecified
- 2,443 raters across audio-only, visual-only, audio-visual

### IEMOCAP
- Categorical: anger, happiness, sadness, neutral, frustration, excitement, surprise
- Dimensional: VAD on continuous scales
- Utterance-level and turn-level annotations
