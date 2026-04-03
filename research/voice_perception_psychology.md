# Psychology and Neuroscience of Voice Perception
## Research Synthesis for Voice Agent Selection System

---

## 1. Thin-Slice Voice Judgments

### Key Research
**McAleer, Todorov & Belin (2014)** - "How Do You Say 'Hello'? Personality Impressions from Brief Novel Voices" (PLOS ONE)

### Core Findings
- People form reliable personality judgments from **sub-second voice samples** (average 391ms — less than half a second)
- 320 participants rated 64 speakers saying just "hello" on 10 traits: aggressiveness, attractiveness, competence, confidence, dominance, femininity, likeability, masculinity, trustworthiness, and warmth
- **Inter-rater reliability was extremely high** (all Cronbach's alphas > 0.88), meaning listeners broadly agree on what personality a voice conveys
- Personality ratings showed "moderate to strong correlations" between one-word (~500ms) and full-sentence (~3000ms) utterances, meaning first impressions are stable and don't change much with more exposure
- Content had minimal impact — ratings were highly correlated regardless of whether speakers used neutral passages or socially-relevant material

### The Two-Dimensional Social Voice Space
All 10 traits collapsed into two orthogonal dimensions explaining ~88% of variance:

1. **Valence (PC1)**: Trustworthiness and likeability loaded positively. This is the warmth/trust axis.
2. **Dominance (PC2)**: Aggressiveness, confidence, and dominance loaded positively; likeability/trustworthiness loaded negatively. This is the power/authority axis.

### Practical Implications for Voice Agent Design
- Voice selection is a sub-second decision by the user — the voice makes its impression before the first sentence is complete
- Every voice can be mapped onto a warmth-dominance space
- You cannot optimize a single voice for both maximum warmth AND maximum authority — they are orthogonal dimensions
- The voice effectively IS the brand personality of the agent

---

## 2. Voice and Trust

### Key Research
- McAleer et al. (2014) — PLOS ONE
- Trustworthiness acoustic analysis (PLOS ONE, 2017) — f0 contour study
- Vocal trustworthiness and acoustic features (PLOS ONE, 2019) — comprehensive acoustic predictors
- Maltezou-Papastylianou et al. (2025) — voice acoustics impact trust in both humans and machines

### Core Findings

**Pitch and Trust — The relationship is nuanced, not simple:**
- The research is MIXED on whether lower or higher pitch = more trustworthy
- The f0 contour study found trustworthiness correlates with a distinctive pitch PATTERN: "high starting f0 then a marked decrease at mid-utterance to finish on a strong rise" (r = 0.99 correlation with perceived trustworthiness)
- It's not just average pitch — it's the dynamic contour (how pitch moves through an utterance)

**The Four Strongest Acoustic Predictors of Trustworthiness** (from the 2019 PLOS ONE study):
| Feature | Direction | Effect Size (beta) |
|---------|-----------|-------------------|
| Speech rate | Faster = more trustworthy | -0.61 |
| Harmonic-to-noise ratio (HNR) | Lower = more trustworthy | -0.43 |
| Fundamental frequency (f0) mean | Lower = more trustworthy | -0.40 |
| F0 standard deviation | Smaller = more trustworthy | -0.14 |

**Critical finding:** "Speech rate was as if not more important than speaker affect, age, and sex" in predicting trustworthiness.

**Speaker Demographics and Trust:**
- Younger speakers received significantly higher trustworthiness ratings (beta = 0.60)
- Female voices were rated more trustworthy than male voices (though effect was sentence-dependent)

**Exposure Effect:**
- Boduch-Grabka & Lev-Ari (2021) found that brief exposure to unfamiliar vocal styles can counteract initial trust biases — familiarity breeds trust

### Practical Implications for Voice Agent Design
- For maximum trust: moderate-to-slightly-lower pitch, slightly faster speaking rate, consistent pitch (low f0 SD), and a natural intonation contour (high-start, dip, rise)
- Speech rate matters MORE than pitch for trust — don't just focus on getting a deep voice
- The pitch contour pattern matters more than absolute pitch level
- Trust in voice is partly about processing fluency — voices that are easy to process feel more trustworthy

---

## 3. Voice and Competence

### Key Research
- McAleer et al. (2014) — competence as one of the 10 rated traits
- Nuyen et al. (2026) — surgeon vocal pitch and perceived intelligence/competence
- Anderson & Klofstad (2012) — voice pitch and leadership competence
- Laustsen, Petersen & Klofstad (2015) — voice pitch and political competence

### Core Findings
- Competence loaded on BOTH dimensions of the social voice space — it's a blend of warmth (being likeable/trustworthy) and dominance (being confident/assertive)
- Lower-pitched voices are consistently perceived as more competent in leadership contexts
- In political elections, candidates with lower-pitched voices were preferred, especially in conservative countries (Banai et al., 2018)
- The preference for lower pitch in leaders holds even for "feminine leadership roles" — voters preferred female candidates with lower (more masculine) voices for school board positions

**Acoustic Features Linked to Perceived Competence:**
- Lower fundamental frequency (f0)
- Moderate speaking rate (not too fast, not too slow)
- Low vocal fry (creaky voice undermines competence)
- Clear articulation / high speech intelligibility
- Confident intonation (declarative patterns, not uptalk)

### Practical Implications for Voice Agent Design
- For competence-focused agents (financial advisor, medical info, technical support): select voices with lower pitch range, clear articulation, moderate pace
- Avoid vocal fry and uptalk patterns
- Competence perception is the sweet spot where warmth meets authority — aim for the middle of the voice space

---

## 4. Voice and Warmth

### Key Research
- McAleer et al. (2014) — warmth within the valence dimension
- PLOS ONE trustworthiness/acoustic study (2019) — warmth-related acoustic features

### Core Findings
Warmth loaded heavily on the **Valence (PC1)** dimension alongside trustworthiness and likeability.

**Acoustic Features Predicting Warmth/Valence:**

For **female voices**, warmth is predicted by:
- Rising intonation (positive loading on intonation, b=0.6)
- Pitch glide (b=-0.58)
- Harmonic-to-noise ratio (HNR, b=-0.44)
- These three features explained **68% of variance** in perceived warmth

For **male voices**, warmth is predicted by:
- Higher average pitch (f0, b=0.48) — note: HIGHER pitch for male warmth
- Harmonic-to-noise ratio (HNR, b=-0.57)
- These explained **49% of variance**

**Key insight:** Warm male voices have HIGHER pitch than dominant male voices. The deepest male voices sound dominant/authoritative, not warm. Warm male voices are in the mid-range.

**Warmth-related vocal behaviors:**
- More pitch variation (dynamic, expressive intonation)
- Slightly higher pitch than baseline (especially for males)
- Breathy voice quality (higher HNR)
- Moderate-to-slightly-faster speaking rate
- Rising intonation patterns (especially for female voices)

### Practical Implications for Voice Agent Design
- For warmth-focused agents (customer support, wellness, companion): select voices with expressive intonation, mid-range pitch, slightly breathy quality
- Male warm voices should NOT be the deepest available — aim mid-range
- Female warm voices benefit from dynamic pitch variation and rising intonation
- Warmth and authority are largely orthogonal — designing for one sacrifices the other

---

## 5. Voice and Authority/Dominance

### Key Research
- McAleer et al. (2014) — dominance dimension (PC2)
- Anderson & Klofstad (2012) — masculine voices preferred for leadership
- Banai et al. (2018) — lower pitch wins elections in conservative countries
- Laustsen et al. (2015) — ideology moderates voice pitch preference

### Core Findings

**Acoustic Features Predicting Dominance (PC2):**

For **male voices** (68% variance explained):
- Lower average pitch (f0)
- Reduced formant dispersion (closer formant spacing = larger perceived body size)
- Decreased alpha ratio
- Lower harmonic-to-noise ratio (HNR)

For **female voices** (27% variance explained):
- Increased pitch (counter-intuitively, higher pitch for female dominance)
- Decreased formant dispersion

**The leadership voice pattern:**
- Lower fundamental frequency
- Narrower formant dispersion (signals larger body size)
- Louder vocal intensity
- Less pitch variation (steady, unwavering)
- Slower, more deliberate speaking rate
- Declarative (falling) intonation patterns

**Political/Leadership Context:**
- "The influence of voice pitch on perceptions of leadership capacity is largely consistent across different domains of leadership"
- Lower-pitched candidates have electoral advantages, especially in presidential races
- Conservative voters show stronger preference for lower-pitched voices
- This preference holds even for traditionally feminine leadership roles

### Practical Implications for Voice Agent Design
- For authority-focused agents (legal, security, compliance, executive): select voices with lower pitch, steady intonation, slower pace
- Male authority = deepest voices with steady pitch
- Female authority is harder to achieve acoustically (only 27% variance explained by measurable features)
- Authority voices should minimize pitch variation — steady and deliberate
- There is a real trade-off: the most authoritative voice will NOT be the warmest

---

## 6. Voice Gender Effects

### Key Research
- Spielmann & Stern (2026) — gender stereotypicality preferences in AI
- Immel et al. (2025) — healthcare voice assistant preferences
- Julie Carpenter (cited in NPR Q article) — task-dependent gender preferences
- Q Project (2019) — first gender-neutral AI voice

### Core Findings

**Gender-Stereotypical Preferences Persist:**
- Users "preferred feminine voices to answer questions in feminine domains" (Spielmann & Stern, 2026)
- In healthcare, respondents "preferred a female assistant or wanted the option" to choose
- Female voices are generally preferred for assistive/caring tasks
- Male voices are generally preferred for authoritative/expert tasks

**Task-Dependent Preferences:**
- Female voices preferred for: customer support, wellness, education, personal assistance
- Male voices preferred for: financial advice, security, technical authority, navigation
- These preferences reflect societal stereotypes, not acoustic reality

**The Gender-Neutral Voice (Q):**
- Created by researchers, sound designers, and linguists with Copenhagen Pride
- Recorded dozens of voices of people who identify as male, female, transgender, or nonbinary
- The fundamental frequency range for gender-neutral perception falls roughly between 145-175 Hz (between typical male ~85-155 Hz and female ~165-255 Hz ranges)
- Creating natural-sounding gender-neutral voice is technically challenging — "your brain can tell if the voice has been pitched up and down"

**Gender Differences in Voice Evaluation:**
- Female listeners rated synthesized voices more positively overall (Kuhne et al., 2020)
- Women showed less discrimination between male voices differing in pitch
- Male vocal attractiveness = combination of warmth AND dominance
- Female vocal attractiveness = primarily warmth/valence

### Practical Implications for Voice Agent Design
- Default to offering choice rather than imposing a gendered voice
- Match voice gender to domain expectations if you must choose (but acknowledge this perpetuates stereotypes)
- Gender-neutral voices (~145-175 Hz) are a viable option but require careful synthesis to avoid uncanny valley
- Consider that your user base's gender composition may affect preferences
- Progressive brands may deliberately choose counter-stereotypical voices

---

## 7. Voice Age Effects

### Key Research
- PLOS ONE (2019) — speaker age and trustworthiness ratings
- Gordon et al. (2019) — speech-language predictors of perceived age
- Harnsberger et al. (2008) — acoustic parameters signaling chronological age

### Core Findings

**Younger Voices Are Rated More Trustworthy:**
- Younger speakers received significantly higher trustworthiness ratings than older speakers (beta = 0.60) — this was a strong effect
- This held across different sentence types

**How Age Is Perceived in Voice:**
- Speaking rate decreases with age
- Fundamental frequency changes (lowers in women, may raise in older men)
- Voice quality deteriorates (more breathiness, tremor, reduced loudness)
- Formant frequencies shift
- Listeners can estimate speaker age with moderate accuracy from voice alone

**Age-Related Acoustic Changes:**
- Increased jitter and shimmer (micro-perturbations in pitch and amplitude)
- Reduced vocal intensity range
- Slower articulation rate
- More pauses and hesitations
- Changes in harmonic-to-noise ratio

### Practical Implications for Voice Agent Design
- For trust-critical applications: younger-sounding voices (25-40 perceived age range) perform best
- For authority/expertise applications: slightly older voices (40-55 perceived age range) may convey experience
- Avoid voices that sound too young (< 25) — may undermine credibility
- Avoid voices with obvious age-related vocal deterioration — reduced clarity hurts all metrics
- The ideal "agent voice" age is likely 28-45 perceived age — young enough for trust, old enough for competence

---

## 8. Accent and Dialect Effects

### Key Research
- Lorenzoni et al. (2022) — foreign accents trigger outgroup categorization
- Frances, Costa & Baus (2018) — accents affect memory and credibility
- Boduch-Grabka & Lev-Ari (2021) — exposure reduces foreign accent bias
- Processing fluency theory (Lev-Ari & Keysar, 2010 — foundational work)

### Core Findings

**The Processing Fluency Effect:**
- "People are more likely to believe things that are easier to process"
- Non-native/unfamiliar accents create processing difficulty, which the brain misattributes to reduced credibility
- This is a cognitive bias, not a rational assessment
- "Foreign-accented speech categorizes the speaker as an outgroup individual with a lower linguistic competence"

**Accent Triggers Social Categorization:**
- Accents immediately signal in-group vs. out-group membership
- Out-group accents face assumptions of "reduced language proficiency"
- This affects perceived trustworthiness, competence, and intelligence
- The bias operates automatically and unconsciously

**The Exposure Effect — Accent Bias Can Be Reduced:**
- Brief familiarization with a foreign accent reduces the credibility penalty
- "Ensuring exposure to foreign accent can reduce discrimination against nonnative speakers"
- The improvement comes from enhanced cognitive processing (easier to understand = more trustworthy)
- This suggests that users may warm up to accented voices over repeated interactions

**Accent Hierarchy (from broader sociolinguistic research):**
- Standard/prestige accents are rated highest for competence (e.g., Received Pronunciation in UK, Standard American English in US)
- Regional accents are often rated higher for warmth/friendliness but lower for competence
- Foreign accents face the largest credibility penalties
- Accent effects interact with the listener's own accent — familiarity is key

### Practical Implications for Voice Agent Design
- **Default to the prestige/standard accent of the target market** for maximum trust and competence
- For warmth-focused agents: regional accents can be a strategic advantage (e.g., Southern US accents perceived as warmer)
- For international markets: use the local standard accent, not a foreign one
- If using accented voices, ensure high articulation clarity to minimize processing fluency penalties
- Users who regularly interact with the voice will develop tolerance for initially unfamiliar accents
- Consider offering accent options that match the user's own regional background
- Never use accents that the target audience would perceive as "foreign" for trust-critical applications

---

## 9. Uncanny Valley in Voice

### Key Research
- Kuhne, Fischer & Zhou (2020) — "The Human Takes It All: Humanlike Synthesized Voices Are Perceived as Less Eerie and More Likable" (Frontiers in Neurorobotics)
- Schreibelmayr & Mara (2022) — "Robot Voices in Daily Life"
- Cohn & Zellou (Interspeech 2020) — concatenative vs. neural TTS perception
- Mittag & Moller (Interspeech 2020) — deep learning assessment of speech naturalness

### Core Findings

**The Uncanny Valley May Work DIFFERENTLY for Voice Than for Faces:**
- Contrary to the traditional uncanny valley hypothesis, "humanlike synthesized voices are perceived as less eerie and more likable"
- Increased human-likeness in voice generally ENHANCES acceptance (unlike the dip seen with visual humanoid robots)
- "When the ratings of human-likeness for both the voice and the speaker characteristics were higher, they seemed less eerie to the participants"

**What Makes Synthetic Voices Eerie:**
- Inconsistency between human-like and robotic features (some aspects sound human, others don't)
- Prosodic flatness with human-sounding timbre (the mismatch is what's creepy)
- Unnatural pauses, rhythm, or emphasis patterns
- Perfectly regular timing (real speech has micro-variations)
- Breathing patterns that don't match speech rhythm

**What Makes Synthetic Voices Acceptable:**
- Users assigned real human names to more lifelike voices (e.g., "Julia" instead of "T380")
- Higher human-likeness = higher acceptance (no uncanny valley dip observed in voice)
- Female participants rated synthesized voices more positively overall
- "Interest in social robots and attitudes toward robots played almost no role in voice evaluation" — meaning pre-existing tech attitudes don't predict voice acceptance

**Neural TTS vs. Concatenative TTS:**
- Neural TTS systems produce more natural-sounding speech
- Listeners perceive meaningful differences between synthesis methods
- Modern neural TTS largely avoids the uncanny valley by achieving consistently high naturalness

**Key Diagnostic Features to Get Right:**
- Prosodic naturalness (rhythm, stress, intonation)
- Breathing and pause patterns
- Micro-variation in timing and pitch (not too perfect)
- Consistent quality across the full utterance

### Practical Implications for Voice Agent Design
- **Push for maximum naturalness** — the uncanny valley is less of a risk in voice than in visual appearance
- Use neural TTS over concatenative approaches
- The biggest risk is INCONSISTENCY — a voice that sounds human in some ways but robotic in others
- Add natural disfluency patterns (breath sounds, micro-pauses) rather than perfectly smooth delivery
- Don't deliberately make the voice sound "robotic" to set expectations — more human-like is consistently preferred
- Monitor for prosodic artifacts (unnatural emphasis, wrong stress patterns) — these are the primary source of eeriness

---

## 10. Cultural Differences in Voice Preference

### Key Research
- Anikin, Aseyev & Erben Johansson (2023) — "Do some languages sound more beautiful than others?" (PNAS)
- Broader sociolinguistic and cross-cultural perception research

### Core Findings

**Limited Cross-Cultural Consensus:**
- Ratings by English, Chinese, and Semitic speakers were "weakly correlated, indicating some cross-cultural concordance in phonesthetic judgments"
- "Overall there was little consensus between raters about which languages sounded more beautiful"
- Cultural background substantially influences voice preferences

**What Appears Universal vs. Culture-Specific:**

Likely Universal:
- The two-dimensional voice space (warmth vs. dominance) appears to be a robust structure across cultures
- Lower pitch = more dominant is consistent across studied cultures
- Processing fluency effects (easier to understand = more trusted)
- The speed of impression formation (~500ms) appears universal

Culture-Specific:
- Which pitch range is "ideal" for warmth or trust
- Accent/dialect prestige hierarchies
- Gender preferences for voice agents
- Preferred speaking rate
- Attitudes toward vocal expressiveness vs. restraint
- What counts as "authoritative" vs. "aggressive"

**Regional Considerations:**
- East Asian markets may prefer softer, higher-pitched female voices for service contexts
- Western markets show stronger preference for lower-pitched voices in authority contexts
- Middle Eastern markets may have stronger gender-role expectations for voice agents
- Latin American markets may prefer more vocal expressiveness and warmth

### Practical Implications for Voice Agent Design
- **Do not assume one voice works globally** — localize voice selection per market
- The warmth-dominance framework is a useful universal scaffold, but the ideal position on each axis varies by culture
- Conduct market-specific voice testing before launch
- Consider that diaspora communities may have hybrid preferences
- Speaking rate norms vary by language — match the local norm

---

## Summary: The Voice Selection Framework

### The Two Fundamental Dimensions
Every voice can be mapped onto a 2D space:
- **X-axis: Warmth/Valence** (trust, likeability, approachability)
- **Y-axis: Dominance/Authority** (competence, confidence, power)

### Acoustic Parameters That Matter Most

| Parameter | Warmth Effect | Authority Effect | Trust Effect |
|-----------|--------------|-----------------|--------------|
| **Pitch (f0)** | Mid-range (higher for males) | Lower | Lower (but contour matters more) |
| **Pitch variation** | More variation = warmer | Less variation = more authoritative | Less variation = more trustworthy |
| **Speaking rate** | Moderate | Slower | Faster (strongest predictor!) |
| **HNR** | Higher (breathier) | Lower (clearer) | Lower |
| **Formant dispersion** | No strong effect | Less dispersion = more dominant | No strong effect |
| **Intonation contour** | Rising patterns | Falling/declarative | High-start, dip, rise |
| **Loudness** | Moderate | Louder | Moderate |

### Decision Matrix for Use Cases

| Use Case | Warmth | Authority | Recommended Voice Profile |
|----------|--------|-----------|--------------------------|
| Customer support | HIGH | Low | Mid-pitch, expressive, moderate-fast pace, warm timbre |
| Financial advisor | Medium | HIGH | Lower pitch, steady intonation, deliberate pace |
| Healthcare companion | HIGH | Medium | Mid-pitch, gentle pace, breathy quality, rising intonation |
| Legal/compliance | Low | HIGH | Low pitch, slow, declarative, minimal variation |
| Sales/marketing | HIGH | Medium | Dynamic pitch, faster pace, energetic, expressive |
| Technical support | Medium | Medium | Clear articulation, moderate pitch, steady pace |
| Executive assistant | Medium | HIGH | Lower pitch, confident, moderate pace, minimal filler |

### Critical Design Principles

1. **Sub-second impression**: The voice makes its impression in <500ms. There is no "getting used to it" — either it fits or it doesn't.
2. **Trade-off is real**: You cannot maximize both warmth and authority in a single voice. Pick the priority for each use case.
3. **Speech rate > pitch for trust**: Speaking rate is the strongest predictor of trustworthiness, yet most voice selection focuses on pitch.
4. **Naturalness wins**: For synthetic voices, push for maximum human-likeness. The uncanny valley is less of a risk in voice than in visual appearance.
5. **Accent = identity**: The accent immediately signals in-group/out-group. Default to the prestige accent of the target market.
6. **Gender is loaded**: Gender preferences exist but are stereotypical and task-dependent. Offer choice when possible.
7. **Age sweet spot**: Perceived age 28-45 balances trust (younger) and competence (not too young).
8. **Culture matters**: Localize voice selection per market. The framework is universal; the ideal settings are not.
9. **Consistency over perfection**: In synthetic voices, inconsistency (some features human, some robotic) is worse than uniformly slightly-less-natural.
10. **Exposure helps**: Users develop tolerance and even preference for initially unfamiliar voices over repeated interaction.
