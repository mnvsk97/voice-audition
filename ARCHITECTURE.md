# Voice Selection Platform — Technical Architecture

## 1. Provider API Research Summary

### 1.1 ElevenLabs (11,309+ voices)

**API Endpoint:** `GET https://api.elevenlabs.io/v1/shared-voices`

**Query Parameters:** page_size, cursor-based pagination via `last_sort_id`

**Response fields per voice:**
- `voice_id`, `name`, `description`
- `accent`, `gender`, `age`, `language`, `locale`
- `descriptive` (tags like "raspy", "deep")
- `use_case` (e.g. "narration", "conversational")
- `category` (e.g. "professional", "generated")
- `preview_url` — FREE audio preview included
- `image_url`
- `rate`, `fiat_rate` — pricing info
- `usage_character_count_1y`, `usage_character_count_7d` — popularity signals
- `cloned_by_count` — popularity signal
- `verified_languages[]` — each with its own `preview_url`, `model_id`, `accent`, `locale`
- `featured`, `free_users_allowed`

**Verdict:** Richest metadata of any provider. Free previews. Cursor pagination handles 11K+ voices. No auth required for shared voices endpoint.

---

### 1.2 PlayHT

**API Endpoint:** `GET https://api.play.ht/api/v2/voices`

**Auth:** API key + user ID headers required

**Response fields per voice:**
- `id`, `name`
- `language`, `language_code`
- `sample` — nullable audio preview URL (FREE when present)
- `accent`, `age`, `gender`
- `loudness`, `style`, `tempo`, `texture`

**Verdict:** Good metadata richness. Audio preview included for most voices. No server-side filtering — client must filter. Separate endpoint for cloned voices.

---

### 1.3 Rime (562 voices across 3 model families)

**API Endpoint:** `GET https://users.rime.ai/data/voices/all-v2.json` (static JSON, no auth)

**Structure:** Three collections: `mist` (140), `mistv2` (160), `arcana` (262)
- Organized by language code: `eng`, `spa`, `fra`, `ger`, `hin`, `ara`, `heb`, `jpn`, `por`
- Values are arrays of voice name strings only

**Metadata available:** NONE — just voice name strings. No gender, age, accent, style, or audio previews. Names are evocative (e.g. "bayou", "glacier", "benjamin") but not structured.

**Verdict:** Minimal metadata. Must generate previews ourselves. Must infer/generate metadata via audio analysis or LLM tagging.

---

### 1.4 Deepgram Aura (91+ voices, no listing API)

**No programmatic voice listing API.** Voices documented statically.

**Voice ID format:** `aura-2-{name}-{lang}` (e.g. `aura-2-thalia-en`)

**Known inventory:**
- English: 41 voices (40 Aura-2 + 12 Aura-1 legacy, some overlap)
- Spanish: 17 voices (Mexican, Peninsular, Colombian, Argentine, Latin American)
- German: 7, French: 2, Dutch: 9, Italian: 10, Japanese: 5

**Metadata available:** Voice name, language, accent descriptor (from docs). No gender, age, style, or preview URLs from API.

**Verdict:** Must maintain a hardcoded registry. Scrape docs for accent metadata. Generate previews ourselves.

---

### 1.5 OpenAI (13 voices, no listing API)

**Voices:** alloy, ash, ballad, cedar, coral, echo, fable, marin, nova, onyx, sage, shimmer, verse

**Models:** `tts-1` (fast, lower quality), `tts-1-hd` (higher quality), `gpt-4o-mini-tts` (with instructions)

**Special feature:** `gpt-4o-mini-tts` accepts an `instructions` parameter for voice style control (e.g. "speak in a warm, empathetic tone").

**Metadata available:** Voice name only. No gender, age, accent, or preview URLs from API.

**Verdict:** Hardcoded registry. Must generate previews. The `instructions` feature is unique and worth surfacing in the platform. Should pre-generate multiple instruction variants per voice as "virtual voices."

---

### 1.6 Azure Speech Service (500+ voices)

**API Endpoint:** `GET https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list`

**Auth:** `Ocp-Apim-Subscription-Key` header or Bearer token

**Response fields per voice:**
- `Name` (full qualified name), `DisplayName`, `LocalName`
- `ShortName` (e.g. `en-US-JennyNeural`)
- `Gender`, `Locale`, `LocaleName`
- `StyleList[]` — speaking styles (e.g. "angry", "cheerful", "sad", "assistant", "chat")
- `RolePlayList[]` — role personas (e.g. "Narrator", "YoungAdultMale")
- `SampleRateHertz`, `VoiceType` (Neural/Standard)
- `Status` (GA/Preview)
- `WordsPerMinute`
- `SecondaryLocaleList[]` — multilingual voices
- `ExtendedPropertyMap` (e.g. IsHighQuality48K)

**No preview URLs.** Must generate ourselves.

**Verdict:** Excellent structured metadata — especially StyleList and RolePlayList. Programmatic listing. Region-specific endpoints.

---

### 1.7 Google Cloud TTS

**API Endpoint:** `GET https://texttospeech.googleapis.com/v1/voices`

**Auth:** OAuth2 with `cloud-platform` scope

**Query params:** Optional `languageCode` filter

**Response fields per voice:**
- `name` (e.g. `en-US-Chirp3-HD-Charon`)
- `languageCodes[]`
- `ssmlGender` (MALE, FEMALE, NEUTRAL)
- `naturalSampleRateHertz`

**No preview URLs.** No style, age, accent, or description metadata.

**Verdict:** Minimal metadata. Programmatic listing. Must generate previews and augment metadata.

---

### 1.8 Amazon Polly

**API Endpoint:** `GET https://polly.{region}.amazonaws.com/v1/voices`

**Auth:** AWS Signature V4

**Query params:** `Engine` (standard/neural/long-form/generative), `LanguageCode`, pagination via `NextToken`

**Response fields per voice:**
- `Id`, `Name`
- `LanguageCode`, `LanguageName`
- `Gender`
- `SupportedEngines[]`
- `AdditionalLanguageCodes[]`

**No preview URLs.** No style, age, accent, or description.

**Verdict:** Minimal metadata. Programmatic listing with pagination. Must generate previews and augment metadata.

---

## 2. Unified Voice Schema

### 2.1 Normalized Data Model

```typescript
interface UnifiedVoice {
  // === Identity ===
  id: string;                          // Platform-unique: "{provider}:{provider_voice_id}"
  provider: Provider;                  // enum: elevenlabs | playht | cartesia | rime | deepgram | openai | azure | google | polly
  provider_voice_id: string;          // Original ID from provider
  provider_model: string;             // e.g. "eleven_turbo_v2_5", "sonic-3", "aura-2", "tts-1-hd"

  // === Display ===
  name: string;                        // Human-readable name
  description: string | null;          // Voice description (from provider or LLM-generated)

  // === Demographics ===
  gender: "male" | "female" | "neutral" | "unknown";
  age_group: "child" | "young_adult" | "adult" | "senior" | "unknown";
  accent: string | null;               // e.g. "American", "British", "Australian"

  // === Language ===
  languages: LanguageSupport[];        // All supported languages
  primary_language: string;            // BCP-47 tag, e.g. "en-US"

  // === Voice Characteristics (normalized 0-1 scale) ===
  characteristics: {
    pitch: number | null;              // 0=deep, 1=high
    speed: number | null;              // 0=slow, 1=fast
    energy: number | null;             // 0=calm, 1=energetic
    warmth: number | null;             // 0=cold/formal, 1=warm/friendly
    clarity: number | null;            // 0=breathy/rough, 1=crystal clear
  };

  // === Style & Use Case ===
  styles: string[];                    // e.g. ["conversational", "narration", "newscast"]
  use_cases: string[];                 // e.g. ["voice_agent", "audiobook", "announcement"]
  tags: string[];                      // Free-form: ["raspy", "deep", "soothing", "professional"]

  // === Audio Previews ===
  previews: {
    standard: string;                  // CDN URL to standard sample (same text across all voices)
    provider_original: string | null;  // Original provider preview URL if available
  };

  // === Quality & Performance ===
  quality_tier: "premium" | "standard" | "basic";
  sample_rate_hz: number;
  supports_streaming: boolean;
  supports_ssml: boolean;
  typical_latency_ms: number | null;   // TTFA measured by our benchmarks

  // === Provider-Specific ===
  provider_metadata: Record<string, any>;  // Raw provider fields we don't normalize

  // === Pipecat Integration ===
  pipecat: {
    supported: boolean;
    service_class: string;             // e.g. "ElevenLabsTTSService"
    config_snippet: Record<string, any>; // Ready-to-use config
  };

  // === Index Metadata ===
  popularity_score: number;            // 0-1, derived from usage stats where available
  last_verified: string;               // ISO timestamp of last sync verification
  status: "active" | "deprecated" | "preview";

  // === Embedding for Semantic Search ===
  text_embedding: number[];            // 768-dim embedding of description+tags for semantic search
  audio_embedding: number[];           // Audio feature embedding for "sounds like" search
}

interface LanguageSupport {
  code: string;                        // BCP-47
  name: string;
  native: boolean;                     // Primary vs secondary language
  preview_url: string | null;
}

type Provider =
  | "elevenlabs" | "playht" | "cartesia" | "rime"
  | "deepgram" | "openai" | "azure" | "google" | "polly";
```

### 2.2 Metadata Coverage Matrix

| Field              | ElevenLabs | PlayHT | Rime | Deepgram | OpenAI | Azure | Google | Polly |
|--------------------|:----------:|:------:|:----:|:--------:|:------:|:-----:|:------:|:-----:|
| name               | Y          | Y      | Y    | Y        | Y      | Y     | Y      | Y     |
| gender             | Y          | Y      | --   | --       | --     | Y     | Y      | Y     |
| age                | Y          | Y      | --   | --       | --     | --    | --     | --    |
| accent             | Y          | Y      | --   | partial  | --     | via locale | --  | --    |
| language           | Y          | Y      | Y    | Y        | --     | Y     | Y      | Y     |
| style/tags         | Y          | Y      | --   | --       | --     | Y     | --     | --    |
| use_case           | Y          | Y      | --   | --       | --     | --    | --     | --    |
| description        | Y          | --     | --   | --       | --     | --    | --     | --    |
| preview_url        | Y (free)   | Y (free)| --  | --       | --     | --    | --     | --    |
| popularity         | Y          | --     | --   | --       | --     | --    | --     | --    |
| sample_rate        | --         | --     | --   | --       | --     | Y     | Y      | --    |
| speaking_styles    | --         | --     | --   | --       | --     | Y     | --     | --    |

**Gap-filling strategy:** See Section 2.3.

### 2.3 Automated Metadata Enrichment Pipeline

For providers with minimal metadata (Rime, Deepgram, OpenAI, Google, Polly):

```
┌─────────────────────────────────────────────────────────────┐
│                  ENRICHMENT PIPELINE                         │
│                                                              │
│  1. Generate audio sample using provider API                 │
│     └─ Standard text: "The quick brown fox jumps over the   │
│        lazy dog. She sells seashells by the seashore."       │
│                                                              │
│  2. Audio Analysis (pyAudioAnalysis / librosa)               │
│     ├─ Fundamental frequency (F0) → pitch classification     │
│     ├─ Speaking rate (WPM) → speed classification            │
│     ├─ Energy/RMS → energy classification                    │
│     └─ Spectral features → voice texture embedding           │
│                                                              │
│  3. LLM Classification (Claude Haiku, batch API)             │
│     ├─ Input: audio transcription + acoustic features        │
│     ├─ Output: gender, age_group, accent, warmth, clarity    │
│     ├─ Output: style tags, use_case recommendations          │
│     └─ Output: natural-language description                  │
│                                                              │
│  4. Audio Embedding (CLAP or custom model)                   │
│     └─ 512-dim embedding for "sounds like" similarity search │
│                                                              │
│  5. Text Embedding (voyage-3-lite on description+tags)       │
│     └─ 768-dim embedding for semantic search                 │
└─────────────────────────────────────────────────────────────┘
```

**Cost estimate for enrichment:**
- Rime: 562 voices x $0.002/voice (TTS generation) = ~$1.12
- Deepgram: 91 voices x $0.003/voice = ~$0.27
- OpenAI: 13 voices x 3 models x $0.015/voice = ~$0.59
- Google: ~400 voices x $0.004/voice = ~$1.60
- Polly: ~60 voices x $0.004/voice = ~$0.24
- Azure: ~500 voices (no TTS cost for listing, ~$2.00 for preview generation)
- LLM classification (Haiku batch): ~1,600 voices x $0.001 = ~$1.60
- **Total one-time enrichment: under $10**

---

## 3. Audio Preview Architecture

### 3.1 Provider Preview Availability

| Provider    | Free Preview URL | Action Required                    |
|-------------|:----------------:|------------------------------------|
| ElevenLabs  | YES              | Cache to our CDN (URLs may expire) |
| PlayHT      | YES (nullable)   | Cache to our CDN                   |
| Cartesia    | NO               | Generate + cache                   |
| Rime        | NO               | Generate + cache                   |
| Deepgram    | NO               | Generate + cache                   |
| OpenAI      | NO               | Generate + cache                   |
| Azure       | NO               | Generate + cache                   |
| Google      | NO               | Generate + cache                   |
| Polly       | NO               | Generate + cache                   |

### 3.2 Sample Text Strategy

Use **three standardized sample texts** for all voices to enable fair comparison:

```
SHORT (5s):  "Hi there! Welcome back. How are you feeling today?"
MEDIUM (15s): "The morning sun cast long shadows across the quiet
               street. She paused at the corner, coffee in hand,
               and smiled at the familiar sound of birdsong."
CONVERSATIONAL (10s): "I totally understand how you're feeling.
                       Let's take a moment to talk through this
                       together. There's no rush at all."
```

The CONVERSATIONAL sample is critical for voice agent evaluation — it tests empathy, pacing, and natural turn-taking cues.

### 3.3 Storage Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Generation   │────▶│   R2 / S3        │────▶│ Cloudflare  │
│  Workers      │     │   Object Store   │     │ CDN         │
└──────────────┘     └──────────────────┘     └─────────────┘
                      │                         │
                      │  /previews/             │  Cache-Control:
                      │    {provider}/          │  public, max-age=
                      │      {voice_id}/        │  31536000,
                      │        short.mp3        │  immutable
                      │        medium.mp3       │
                      │        conversational.mp3│
                      └──────────────────┘

Storage estimate:
- ~12,500 voices x 3 samples x ~150KB avg = ~5.6 GB
- CDN egress: Cloudflare R2 = free egress
- Monthly storage: R2 = $0.015/GB = ~$0.09/month
```

**Audio format:** MP3 128kbps for previews (universal browser compatibility), WAV 24kHz 16-bit stored as source of truth.

### 3.4 Preview Generation Pipeline

```python
# Pseudocode for preview generation worker
async def generate_previews(voice: UnifiedVoice):
    for sample_key, sample_text in SAMPLE_TEXTS.items():
        audio = await provider_adapters[voice.provider].synthesize(
            text=sample_text,
            voice_id=voice.provider_voice_id,
            model=voice.provider_model,
            output_format="wav_24khz_16bit"
        )

        # Convert to MP3 for CDN
        mp3 = convert_to_mp3(audio, bitrate=128)

        # Upload to R2
        key = f"previews/{voice.provider}/{voice.provider_voice_id}/{sample_key}.mp3"
        await r2.put(key, mp3, content_type="audio/mpeg")

        # Also run audio analysis for enrichment
        features = extract_audio_features(audio)
        await update_voice_characteristics(voice.id, features)
```

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Next.js App)                         │
│                                                                     │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Voice    │  │ A/B Compare  │  │ Real-time│  │ Pipecat Config│  │
│  │ Browser  │  │ Side-by-Side │  │ Test     │  │ Generator     │  │
│  └────┬─────┘  └──────┬───────┘  └────┬─────┘  └───────┬───────┘  │
│       │               │               │                │           │
└───────┼───────────────┼───────────────┼────────────────┼───────────┘
        │               │               │                │
        ▼               ▼               ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI)                          │
│                                                                     │
│  GET /voices          — search, filter, paginate                    │
│  GET /voices/:id      — full voice detail                           │
│  POST /voices/search  — semantic natural-language search             │
│  POST /voices/compare — side-by-side comparison data                │
│  POST /synthesize     — real-time TTS for custom text               │
│  GET /voices/:id/pipecat-config — integration snippet               │
│  POST /voices/benchmark — trigger latency measurement               │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
┌──────────────────┐ ┌──────────┐  ┌────────────────────┐
│   PostgreSQL     │ │ Typesense│  │  Provider Adapters  │
│   (source of     │ │ (search  │  │                     │
│    truth)        │ │  index)  │  │  ┌─ ElevenLabs     │
│                  │ │          │  │  ├─ PlayHT          │
│  voices          │ │ Fast     │  │  ├─ Cartesia        │
│  voice_previews  │ │ faceted  │  │  ├─ Rime            │
│  voice_benchmarks│ │ search   │  │  ├─ Deepgram        │
│  sync_log        │ │ + typo   │  │  ├─ OpenAI          │
│                  │ │ tolerance│  │  ├─ Azure            │
│                  │ │          │  │  ├─ Google           │
│                  │ │ Semantic │  │  └─ Polly            │
│                  │ │ vector   │  │                      │
│                  │ │ search   │  │  Real-time synth     │
│                  │ │ built-in │  │  + latency probes    │
└──────────────────┘ └──────────┘  └────────────────────┘
```

### 4.2 Technology Choices

| Component           | Technology                  | Rationale                                                    |
|---------------------|-----------------------------|--------------------------------------------------------------|
| API Server          | **FastAPI** (Python)        | Async, fast, typed. Same ecosystem as Pipecat.               |
| Database            | **PostgreSQL 16**           | JSONB for provider_metadata, pg_trgm for fuzzy text search.  |
| Search Engine       | **Typesense**               | Built-in vector search + faceted filtering + typo tolerance. Sub-50ms queries on 12K docs. Self-hostable. Free tier. |
| Object Storage      | **Cloudflare R2**           | S3-compatible, zero egress fees.                             |
| CDN                 | **Cloudflare**              | Automatic with R2. Global edge caching.                      |
| Task Queue          | **Celery + Redis**          | Preview generation, sync jobs, enrichment pipeline.          |
| Frontend            | **Next.js 14 (App Router)** | SSR for SEO, React Server Components for perf.               |
| Audio Player        | **Howler.js**               | Cross-browser audio with Web Audio API fallback.             |
| Monitoring          | **Prometheus + Grafana**    | Track sync health, API latency, search performance.          |

### 4.3 Why Typesense over Alternatives

- **vs. Elasticsearch:** Typesense is purpose-built for search UX — built-in typo tolerance, faceted filtering, and vector search in one engine. 10x simpler to operate.
- **vs. Meilisearch:** Typesense has native vector search support, Meili does not (yet). Critical for semantic "find me a warm, friendly female voice" queries.
- **vs. Pinecone/Weaviate:** Typesense combines keyword + vector + faceted search in one index. No need for a separate vector DB. For 12K documents, a dedicated vector DB is overkill.
- **vs. PostgreSQL full-text:** pg_trgm works for simple text search but cannot do faceted filtering + vector similarity + typo tolerance at the same time with good UX.

### 4.4 Database Schema

```sql
CREATE TABLE voices (
    id TEXT PRIMARY KEY,                    -- "{provider}:{provider_voice_id}"
    provider TEXT NOT NULL,
    provider_voice_id TEXT NOT NULL,
    provider_model TEXT,

    name TEXT NOT NULL,
    description TEXT,

    gender TEXT DEFAULT 'unknown',
    age_group TEXT DEFAULT 'unknown',
    accent TEXT,
    primary_language TEXT NOT NULL DEFAULT 'en-US',
    languages JSONB DEFAULT '[]',

    -- Normalized characteristics (0.0 - 1.0)
    pitch REAL,
    speed REAL,
    energy REAL,
    warmth REAL,
    clarity REAL,

    styles TEXT[] DEFAULT '{}',
    use_cases TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',

    quality_tier TEXT DEFAULT 'standard',
    sample_rate_hz INTEGER,
    supports_streaming BOOLEAN DEFAULT true,
    supports_ssml BOOLEAN DEFAULT false,

    -- Pipecat integration
    pipecat_supported BOOLEAN DEFAULT false,
    pipecat_service_class TEXT,
    pipecat_config JSONB,

    -- Provider-specific raw data
    provider_metadata JSONB DEFAULT '{}',

    -- Embeddings
    text_embedding vector(768),
    audio_embedding vector(512),

    -- Index metadata
    popularity_score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active',
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(provider, provider_voice_id)
);

CREATE TABLE voice_previews (
    id SERIAL PRIMARY KEY,
    voice_id TEXT REFERENCES voices(id),
    sample_type TEXT NOT NULL,               -- 'short', 'medium', 'conversational'
    cdn_url TEXT NOT NULL,
    duration_ms INTEGER,
    file_size_bytes INTEGER,
    generated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE voice_benchmarks (
    id SERIAL PRIMARY KEY,
    voice_id TEXT REFERENCES voices(id),
    measured_at TIMESTAMPTZ DEFAULT now(),
    ttfa_ms INTEGER,                         -- Time to first audio byte
    total_latency_ms INTEGER,                -- Total synthesis time
    rtf REAL,                                -- Real-time factor
    region TEXT,                             -- Where measurement was taken
    input_length_chars INTEGER
);

CREATE TABLE sync_log (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    voices_added INTEGER DEFAULT 0,
    voices_updated INTEGER DEFAULT 0,
    voices_deprecated INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    error_message TEXT
);

-- Indexes
CREATE INDEX idx_voices_provider ON voices(provider);
CREATE INDEX idx_voices_language ON voices(primary_language);
CREATE INDEX idx_voices_gender ON voices(gender);
CREATE INDEX idx_voices_tags ON voices USING gin(tags);
CREATE INDEX idx_voices_styles ON voices USING gin(styles);
CREATE INDEX idx_voices_popularity ON voices(popularity_score DESC);
CREATE INDEX idx_voices_text_embed ON voices USING ivfflat(text_embedding vector_cosine_ops);
CREATE INDEX idx_voices_audio_embed ON voices USING ivfflat(audio_embedding vector_cosine_ops);
```

---

## 5. Search Architecture

### 5.1 Multi-Modal Search

```
User Query: "warm friendly female voice for healthcare calls"
                    │
                    ▼
         ┌─────────────────────┐
         │   Query Classifier  │
         │   (rule-based +     │
         │    embeddings)      │
         └────────┬────────────┘
                  │
     ┌────────────┼────────────────┐
     ▼            ▼                ▼
┌─────────┐ ┌──────────┐  ┌──────────────┐
│ Facet   │ │ Keyword  │  │ Semantic     │
│ Extract │ │ Search   │  │ Vector       │
│         │ │          │  │ Search       │
│ gender: │ │ "warm    │  │              │
│ female  │ │  friendly│  │ embed(query) │
│         │ │  health" │  │ → cosine sim │
└────┬────┘ └────┬─────┘  └──────┬───────┘
     │           │               │
     ▼           ▼               ▼
┌─────────────────────────────────────────┐
│        Typesense Multi-Search           │
│                                         │
│  filter_by: gender:=female              │
│  q: "warm friendly health"              │
│  vector_query: embedding:([], k:50)     │
│  sort_by: _text_match(weight:0.3)       │
│           + _vector_distance(weight:0.5)│
│           + popularity_score(weight:0.2)│
└─────────────────────────────────────────┘
```

### 5.2 Typesense Collection Schema

```json
{
  "name": "voices",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "provider", "type": "string", "facet": true},
    {"name": "name", "type": "string"},
    {"name": "description", "type": "string", "optional": true},
    {"name": "gender", "type": "string", "facet": true},
    {"name": "age_group", "type": "string", "facet": true},
    {"name": "accent", "type": "string", "facet": true, "optional": true},
    {"name": "primary_language", "type": "string", "facet": true},
    {"name": "languages", "type": "string[]", "facet": true},
    {"name": "styles", "type": "string[]", "facet": true},
    {"name": "use_cases", "type": "string[]", "facet": true},
    {"name": "tags", "type": "string[]", "facet": true},
    {"name": "quality_tier", "type": "string", "facet": true},
    {"name": "supports_streaming", "type": "bool", "facet": true},
    {"name": "pipecat_supported", "type": "bool", "facet": true},
    {"name": "popularity_score", "type": "float"},
    {"name": "preview_url", "type": "string", "optional": true, "index": false},
    {"name": "text_embedding", "type": "float[]", "embed": {"from": [], "model_config": {"dims": 768}}},
    {"name": "audio_embedding", "type": "float[]", "num_dim": 512, "optional": true}
  ],
  "default_sorting_field": "popularity_score"
}
```

### 5.3 Search Performance at Scale

For 12,000 voices in Typesense:
- **Faceted keyword search:** <10ms p99
- **Vector search (k=50):** <25ms p99
- **Hybrid (keyword + vector + facets):** <35ms p99
- **Memory footprint:** ~200MB including vectors
- **Index rebuild time:** <5 seconds

This is comfortable for single-node deployment. No sharding needed until 100K+ documents.

---

## 6. Real-Time Voice Testing

### 6.1 "Try This Voice" Architecture

```
┌────────────┐         ┌──────────────┐        ┌──────────────┐
│  Browser   │  POST   │   API        │  TTS   │  Provider    │
│            │────────▶│   /synthesize │───────▶│  API         │
│  <audio>   │◀────────│              │◀───────│              │
│  element   │ stream  │  Measures    │ stream │              │
│            │ (SSE)   │  TTFA + RTF  │        │              │
└────────────┘         └──────────────┘        └──────────────┘
```

**Implementation:**

```python
@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """Stream TTS audio with latency measurement."""
    provider = get_provider_adapter(request.provider)

    t_start = time.monotonic()
    first_byte_received = False

    async def audio_stream():
        nonlocal first_byte_received
        async for chunk in provider.synthesize_stream(
            text=request.text,
            voice_id=request.voice_id,
            model=request.model,
        ):
            if not first_byte_received:
                ttfa = (time.monotonic() - t_start) * 1000
                first_byte_received = True
                # Prepend latency header as first SSE event
                yield f"event: metrics\ndata: {json.dumps({'ttfa_ms': ttfa})}\n\n"
            yield chunk

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={"X-TTFA-Ms": str(ttfa)}
    )
```

### 6.2 Latency Measurement Methodology

**TTFA (Time to First Audio):** Time from API request to first audio byte received at the server. This is the most critical metric for voice agents — it determines perceived responsiveness.

**RTF (Real-Time Factor):** `audio_duration / processing_time`. RTF < 1.0 means faster than real-time (required for streaming).

**Measurement protocol:**
1. Standardized input: "Hello, how can I help you today?" (8 words)
2. Measure from 3 regions (us-east, us-west, eu-west)
3. 5 measurements per voice, discard highest and lowest, average remaining 3
4. Run benchmarks weekly via Celery beat
5. Store results in `voice_benchmarks` table

### 6.3 A/B Comparison UX

```
┌─────────────────────────────────────────────────┐
│           Voice Comparison                       │
│                                                  │
│  ┌─────────────────┐  ┌─────────────────┐       │
│  │ Voice A          │  │ Voice B          │      │
│  │ ElevenLabs       │  │ Cartesia         │      │
│  │ "Rachel"         │  │ "Sonic-3 British" │     │
│  │                  │  │                  │      │
│  │  [▶ Play Short]  │  │  [▶ Play Short]  │     │
│  │  [▶ Play Conv.]  │  │  [▶ Play Conv.]  │     │
│  │                  │  │                  │      │
│  │ TTFA: 142ms      │  │ TTFA: 89ms       │     │
│  │ Gender: Female   │  │ Gender: Female   │      │
│  │ Warmth: 0.8      │  │ Warmth: 0.6      │     │
│  │ Clarity: 0.9     │  │ Clarity: 0.95    │     │
│  └─────────────────┘  └─────────────────┘       │
│                                                  │
│  Custom Text: [________________________________] │
│               [▶ Generate Both]                  │
│                                                  │
│  ┌─ Pipecat Config ──────────────────────────┐  │
│  │ CartesiaTTSService(                        │  │
│  │   voice_id="...",                          │  │
│  │   model="sonic-3",                         │  │
│  │ )                                          │  │
│  └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

Key UX features:
- Synchronized playback: press spacebar to start both simultaneously
- Waveform visualization for visual comparison
- Instant Pipecat config snippet copy for the selected voice
- "Lock" one voice and cycle through candidates for the other

---

## 7. Data Freshness & Sync Strategy

### 7.1 Provider Update Frequency (Estimated)

| Provider    | New Voice Cadence  | Sync Strategy          | Effort |
|-------------|--------------------|-----------------------|--------|
| ElevenLabs  | Daily (community)  | Poll every 6 hours    | High   |
| PlayHT      | Monthly            | Poll daily            | Low    |
| Cartesia    | Quarterly          | Poll weekly           | Low    |
| Rime        | Quarterly          | Poll weekly (JSON)    | Low    |
| Deepgram    | Monthly            | Manual + docs scrape  | Medium |
| OpenAI      | Rare (yearly)      | Manual                | None   |
| Azure       | Monthly            | Poll weekly (API)     | Low    |
| Google      | Monthly            | Poll weekly (API)     | Low    |
| Polly       | Rare               | Poll monthly          | None   |

### 7.2 Sync Architecture

```python
# Celery beat schedule
CELERYBEAT_SCHEDULE = {
    'sync-elevenlabs': {
        'task': 'sync.elevenlabs',
        'schedule': crontab(hour='*/6'),       # Every 6 hours
    },
    'sync-playht': {
        'task': 'sync.playht',
        'schedule': crontab(hour=2, minute=0), # Daily 2am
    },
    'sync-azure': {
        'task': 'sync.azure',
        'schedule': crontab(day_of_week=1, hour=3),  # Weekly Monday 3am
    },
    'sync-google': {
        'task': 'sync.google',
        'schedule': crontab(day_of_week=1, hour=4),
    },
    'sync-rime': {
        'task': 'sync.rime',
        'schedule': crontab(day_of_week=1, hour=5),
    },
    'sync-polly': {
        'task': 'sync.polly',
        'schedule': crontab(day_of_month=1, hour=6), # Monthly
    },
    'sync-deepgram-openai': {
        'task': 'sync.static_providers',
        'schedule': crontab(day_of_month=1, hour=7), # Monthly manual review
    },
    'run-benchmarks': {
        'task': 'benchmark.all_voices',
        'schedule': crontab(day_of_week=0, hour=1),  # Weekly Sunday 1am
    },
}
```

### 7.3 Sync Algorithm

```python
async def sync_provider(provider: str):
    log = SyncLog(provider=provider)

    # 1. Fetch current voices from provider
    remote_voices = await provider_adapters[provider].list_voices()
    remote_ids = {v.provider_voice_id for v in remote_voices}

    # 2. Fetch our current index for this provider
    local_voices = await db.get_voices_by_provider(provider)
    local_ids = {v.provider_voice_id for v in local_voices}

    # 3. Detect changes
    new_ids = remote_ids - local_ids
    removed_ids = local_ids - remote_ids
    existing_ids = remote_ids & local_ids

    # 4. Add new voices
    for voice_id in new_ids:
        voice = next(v for v in remote_voices if v.provider_voice_id == voice_id)
        normalized = normalize_voice(voice)
        await db.insert_voice(normalized)
        # Queue preview generation and enrichment
        generate_previews.delay(normalized.id)
        enrich_metadata.delay(normalized.id)
        log.voices_added += 1

    # 5. Mark removed voices as deprecated (don't delete)
    for voice_id in removed_ids:
        await db.update_voice_status(f"{provider}:{voice_id}", "deprecated")
        log.voices_deprecated += 1

    # 6. Update existing voices (check for metadata changes)
    for voice_id in existing_ids:
        remote = next(v for v in remote_voices if v.provider_voice_id == voice_id)
        local = next(v for v in local_voices if v.provider_voice_id == voice_id)
        if has_metadata_changed(remote, local):
            await db.update_voice(f"{provider}:{voice_id}", normalize_voice(remote))
            log.voices_updated += 1

    # 7. Rebuild Typesense index for this provider
    await rebuild_search_index(provider)

    log.status = "completed"
    await db.save_sync_log(log)
```

### 7.4 Voice Deprecation Handling

Never hard-delete voices. Mark as `status: "deprecated"` with a `deprecated_at` timestamp. Reasons:
- Users may have saved references/bookmarks
- Pipecat configs in the wild may reference the voice
- Show deprecation notice in UI with suggested alternatives (nearest neighbor in embedding space)

---

## 8. Pipecat Integration

### 8.1 Supported Providers in Pipecat

Based on the pipecat repository, these TTS providers have native service classes:

| Provider     | Pipecat Service Class          | Voice Param     | Model Param          |
|--------------|-------------------------------|-----------------|----------------------|
| ElevenLabs   | `ElevenLabsTTSService`        | `voice` (ID)    | `model` ("eleven_turbo_v2_5") |
| Cartesia     | `CartesiaTTSService`          | `voice` (ID)    | `model` ("sonic-3")  |
| Rime         | (in services/)                | `voice`         | model variant        |
| Deepgram     | `DeepgramTTSService`          | `voice`         | `"aura-2-helena-en"` |
| OpenAI       | `OpenAITTSService`            | `voice` ("alloy")| `model` ("gpt-4o-mini-tts") |
| Azure        | `AzureTTSService`             | `voice`         | region-based         |
| Google       | `GoogleTTSService`            | `voice`         | model in voice name  |
| AWS Polly    | (in services/aws/)            | voice ID        | engine               |
| PlayHT       | Not natively supported        | N/A             | N/A                  |

### 8.2 Config Snippet Generator

For each voice, generate a ready-to-paste Pipecat config:

```python
def generate_pipecat_config(voice: UnifiedVoice) -> dict:
    """Generate copy-pasteable Pipecat service configuration."""

    configs = {
        "elevenlabs": {
            "class": "ElevenLabsTTSService",
            "import": "from pipecat.services.elevenlabs import ElevenLabsTTSService",
            "init": {
                "api_key": "os.getenv('ELEVENLABS_API_KEY')",
                "voice_id": voice.provider_voice_id,
                "model": voice.provider_model or "eleven_turbo_v2_5",
            }
        },
        "cartesia": {
            "class": "CartesiaTTSService",
            "import": "from pipecat.services.cartesia import CartesiaTTSService",
            "init": {
                "api_key": "os.getenv('CARTESIA_API_KEY')",
                "voice_id": voice.provider_voice_id,
                "model": voice.provider_model or "sonic-3",
            }
        },
        "deepgram": {
            "class": "DeepgramTTSService",
            "import": "from pipecat.services.deepgram import DeepgramTTSService",
            "init": {
                "api_key": "os.getenv('DEEPGRAM_API_KEY')",
                "voice": voice.provider_voice_id,
            }
        },
        "openai": {
            "class": "OpenAITTSService",
            "import": "from pipecat.services.openai import OpenAITTSService",
            "init": {
                "api_key": "os.getenv('OPENAI_API_KEY')",
                "voice": voice.provider_voice_id,
                "model": voice.provider_model or "gpt-4o-mini-tts",
            }
        },
        "azure": {
            "class": "AzureTTSService",
            "import": "from pipecat.services.azure import AzureTTSService",
            "init": {
                "api_key": "os.getenv('AZURE_SPEECH_KEY')",
                "region": "os.getenv('AZURE_SPEECH_REGION')",
                "voice": voice.provider_voice_id,
            }
        },
        "google": {
            "class": "GoogleTTSService",
            "import": "from pipecat.services.google import GoogleTTSService",
            "init": {
                "credentials": "os.getenv('GOOGLE_APPLICATION_CREDENTIALS')",
                "voice_id": voice.provider_voice_id,
            }
        },
    }

    return configs.get(voice.provider, None)
```

### 8.3 One-Click Pipeline Template

Beyond individual voice config, provide full pipeline templates:

```python
# Generated for: ElevenLabs "Rachel" voice
# Optimized for: Voice Agent (conversational, low latency)

from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.services.anthropic import AnthropicLLMService

stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

llm = AnthropicLLMService(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-sonnet-4-20250514",
)

tts = ElevenLabsTTSService(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
    model="eleven_turbo_v2_5",
)

pipeline = Pipeline([stt, llm, tts])
```

---

## 9. Cost Analysis

### 9.1 Infrastructure Costs (Monthly)

| Component                    | Service               | Monthly Cost  |
|-----------------------------|-----------------------|---------------|
| API Server                  | Railway / Fly.io      | $10-20        |
| PostgreSQL (with pgvector)  | Supabase free / Neon  | $0-25         |
| Typesense                   | Typesense Cloud (free tier covers 12K docs) | $0  |
| Redis                       | Upstash (free tier)   | $0            |
| Object Storage (R2, ~6GB)  | Cloudflare R2         | $0.09         |
| CDN                         | Cloudflare (free)     | $0            |
| Celery Workers              | Railway               | $5-10         |
| **Total infrastructure**    |                       | **$15-55/mo** |

### 9.2 Provider API Costs (Monthly Ongoing)

| Cost Category               | Estimate              |
|----------------------------|-----------------------|
| ElevenLabs sync (free endpoint) | $0               |
| PlayHT sync (free endpoint)| $0                    |
| Real-time TTS for "try it" | $20-50 (usage-based) |
| Weekly benchmarks           | $5-10                |
| Preview regeneration (new voices) | $1-2           |
| LLM enrichment (new voices)| $0.50-1              |
| **Total API costs**        | **$25-65/mo**         |

### 9.3 One-Time Setup Costs

| Task                        | Cost                  |
|----------------------------|-----------------------|
| Initial preview generation  | ~$10                  |
| Initial LLM enrichment     | ~$5                   |
| Audio embedding generation  | ~$3                   |
| **Total setup**            | **~$18**              |

---

## 10. Implementation Roadmap

### Phase 1: Core Index (Week 1-2)
- PostgreSQL schema + provider adapters for ElevenLabs, Cartesia, Deepgram, OpenAI
- Initial data ingestion from all providers
- Basic REST API with filtering
- Preview caching for providers with free URLs

### Phase 2: Search & Previews (Week 3-4)
- Typesense index setup with faceted search
- Preview generation pipeline for providers without free URLs
- LLM metadata enrichment pipeline
- Basic Next.js frontend with voice browser

### Phase 3: Intelligence (Week 5-6)
- Semantic vector search (text embeddings)
- Audio embedding generation and "sounds like" search
- A/B comparison UI
- Pipecat config generator

### Phase 4: Real-Time Testing (Week 7-8)
- Real-time synthesis endpoint with streaming
- TTFA/RTF measurement and display
- Automated weekly benchmarking
- Full sync automation with monitoring

### Phase 5: Polish (Week 9-10)
- OpenAI instruction variants ("virtual voices")
- Deprecation detection and alternative suggestions
- Public API with rate limiting
- SEO optimization for voice discovery pages

---

## 11. Key Technical Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ElevenLabs rate-limiting on shared-voices endpoint | Can't sync 11K voices | Respect rate limits, use cursor pagination, cache aggressively, sync incrementally |
| Provider preview URLs expire | Broken audio in UI | Copy all previews to R2 on ingestion. Never serve provider URLs directly. |
| Cartesia API docs behind auth wall | Can't discover voice listing API | Use Cartesia Python SDK to enumerate voices. Fall back to hardcoded list from their website. |
| LLM metadata enrichment inconsistency | Voices tagged differently across runs | Use structured output with constrained enums. Run enrichment once and lock. Human review for edge cases. |
| Provider adds/removes voices between syncs | Stale index | 6-hour sync for high-churn providers. Deprecation notices rather than deletion. |
| Real-time synthesis cost explosion | Budget overrun | Rate limit per IP. Require auth for custom text synthesis. Cache popular text+voice combinations. |
| Audio embedding model drift | Search quality degrades | Pin model version. Re-embed all voices when upgrading model. |
