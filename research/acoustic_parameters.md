# Acoustic Voice Analysis Parameters

## eGeMAPS (extended Geneva Minimalistic Acoustic Parameter Set)
Source: Eyben, Scherer et al. (2016). 88 features designed as a standardized,
minimalistic set for affective computing and computational paralinguistics.

### 25 Low-Level Descriptors (LLDs)

**Frequency (voiced segments only):**
1. F0semitoneFrom27.5Hz — fundamental frequency on semitone scale
2. jitterLocal — F0 period perturbation
3. shimmerLocaldB — amplitude perturbation in dB
4. HNRdBACF — harmonics-to-noise ratio via autocorrelation
5. logRelF0-H1-H2 — log ratio of 1st to 2nd harmonic (breathiness)
6. logRelF0-H1-A3 — log ratio of 1st harmonic to 3rd formant amplitude
7-15. F1/F2/F3 frequency, bandwidth, amplitude (3 each)

**Energy:**
16. Loudness — perceived loudness (auditory model-based)

**Spectral:**
17. alphaRatio — energy ratio above/below 1 kHz
18. hammarbergIndex — energy peak diff 0-2 kHz vs 2-5 kHz
19-20. slope0-500, slope500-1500 — spectral slopes
21. spectralFlux — frame-to-frame spectral change
22-25. mfcc1-4 — first 4 MFCCs (timbre fingerprint)

### Functionals → 88 Features
- F0 and loudness: mean, stddev, percentiles 20/50/80, range, rising/falling slopes (10 each = 20)
- Spectral flux all frames: mean, stddev (2)
- MFCC1-4 all frames: mean, stddev (8)
- Jitter/shimmer/HNR/H1-H2/H1-A3/F1-F3 voiced: mean, stddev (26)
- Spectral features voiced: mean, stddev (16)
- Spectral features unvoiced: mean only (5)
- Temporal: loudnessPeaksPerSec, VoicedSegmentsPerSec, mean/stddev voiced/unvoiced length, equivalentSoundLevel (7)
- **Total: 88 features**

## Parameter Tiers for Voice Agent Selection

### Tier 1 — Must-have (directly determine voice character)
| Parameter | Perceptual Mapping |
|-----------|-------------------|
| F0 mean | Pitch height → gender, authority, age |
| F0 variability | Expressiveness → extraversion, engagement |
| Speaking rate | Pace → trust, energy, competence |
| Loudness | Power → confidence, intimacy |
| Formants F1-F3 | Vocal tract size → gender, age |
| MFCCs 1-4 | Timbre fingerprint → voice identity |
| HNR | Voice clarity → health, breathiness |

### Tier 2 — Important for nuance
| Parameter | Perceptual Mapping |
|-----------|-------------------|
| H1-H2 | Breathiness/phonation type |
| Alpha ratio | Vocal effort (soft vs pressed) |
| Jitter/shimmer | Voice stability/roughness |
| F0 slopes | Intonation personality (rising=friendly, falling=authoritative) |
| Voiced/unvoiced timing | Rhythm and pausing |

### Tier 3 — Supplementary
Hammarberg index, spectral flux, H1-A3, formant bandwidths, spectral centroid/rolloff/flatness

## GRBAS Scale (Clinical Voice Quality)
Scored 0-3 for each dimension:
- **G** (Grade): Overall abnormality
- **R** (Roughness): Irregular vibration → high jitter/shimmer, low HNR
- **B** (Breathiness): Incomplete closure → high shimmer, low HNR, high H1-H2
- **A** (Asthenia): Weakness → low intensity
- **S** (Strain): Tension → high F0, spectral energy shift upward

## Python Libraries

### librosa
spectral_centroid (brightness), mfcc (timbre), rms (loudness), pyin (pitch),
spectral_bandwidth, spectral_contrast, spectral_flatness, spectral_rolloff,
zero_crossing_rate, tempo

### openSMILE
eGeMAPSv02 (88 features), ComParE 2016 (6,373 features), emobase, IS09-IS13 challenge sets

### Praat/Parselmouth
Gold standard for: formant tracking (F1-F5), jitter (5 variants), shimmer (6 variants),
HNR, intensity contour, pitch with manual correction
