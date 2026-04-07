# voice-audition

The casting director for your AI voice agent. Search voices across multiple TTS providers with Moss-powered text search, a checked-in SQLite catalog, local runtime state, use-case auditions, and cost comparison.

## Install

```bash
pip install voice-audition
pip install voice-audition[enrich]   # adds Qwen2-Audio enrichment
pip install voice-audition[mcp]      # adds MCP server for Claude
pip install voice-audition[acoustic] # adds acoustic analysis
pip install voice-audition[clap]     # adds CLAP embeddings + audio search
```

## Setup

```bash
cp .env.example .env
```

```bash
# Optional: Moss credentials for semantic search
# Get them at https://platform.inferedge.dev
MOSS_PROJECT_ID=...
MOSS_PROJECT_KEY=...

# Optional: Provider API keys for sync + enrichment
ELEVENLABS_API_KEY=...
OPENAI_API_KEY=...
DEEPGRAM_API_KEY=...
RIME_API_KEY=...
CARTESIA_API_KEY=...
PLAYHT_API_KEY=...
PLAYHT_USER_ID=...
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=...
GOOGLE_ACCESS_TOKEN=...
```

## Quick start

```bash
# Sync voices from all providers
voice-audition sync

# Build search index
voice-audition index

# Search
voice-audition search "warm female voice for healthcare"

# Analyze options without generating audio
voice-audition analyze "voice for fertility clinic for anxious IVF patients"

# Search by audio similarity
voice-audition search-audio ./reference.wav

# Run a full audition
voice-audition audition "fertility clinic for anxious IVF patients" --gender female --mode ai
voice-audition audition "fertility clinic for anxious IVF patients" --gender female --mode human

# Compare costs at 100k minutes/month
voice-audition costs 100000
```

## Commands

| Command | What it does |
|---------|-------------|
| `voice-audition sync [providers...]` | Sync voices from TTS providers with diff-based lifecycle tracking |
| `voice-audition index` | Build or rebuild the Moss semantic search index |
| `voice-audition search <query>` | Semantic search the voice catalog (`--top-k` for result count) |
| `voice-audition analyze <brief>` | Deterministic recommendation pass over top candidates without audio generation |
| `voice-audition enrich [providers...]` | Enrich voices with Qwen2-Audio descriptions and traits (`--model`) |
| `voice-audition audition <brief>` | Run a use-case audition with `--mode ai|human` |
| `voice-audition costs <minutes>` | Compare API vs self-hosted costs at a given monthly volume |
| `voice-audition enrich-acoustic [providers...]` | Compute acoustic measurements and store them in SQLite |
| `voice-audition embed [providers...]` | Generate CLAP embeddings and store them in SQLite |
| `voice-audition search-audio <path>` | Find voices acoustically similar to an audio clip |
| `voice-audition monitor` | Check provider reliability via status pages |
| `voice-audition stats` | Show catalog statistics |
| `voice-audition mcp` | Start the MCP server for Claude integration |

## Cost calculator

```bash
$ voice-audition costs 100000

# Compares per-provider API pricing against self-hosted open source:
#   ElevenLabs  100k min = $3,000/mo
#   Cartesia    100k min = $1,500/mo
#   Kokoro      100k min = $0 (self-hosted, GPU cost only)
#   Piper       100k min = $0 (self-hosted, CPU-capable)
```

At high volume, self-hosted open source voices (Kokoro, Piper, Orpheus) can cut costs to near-zero -- the calculator shows the breakeven.

## MCP Server

Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "voice-audition": {
      "command": "voice-audition",
      "args": ["mcp"],
      "env": {
        "MOSS_PROJECT_ID": "...",
        "MOSS_PROJECT_KEY": "..."
      }
    }
  }
}
```

Exposes additive search and analysis tools over the SQLite-backed catalog:

| Tool | What it does |
|------|-------------|
| `search_voices` | Semantic search across the full catalog |
| `analyze_voices` | Deterministic recommendation pass without audio generation |
| `get_voice` | Get detailed info for a specific voice |
| `filter_voices` | Filter by gender, provider, accent, age group, or use case |
| `get_catalog_stats` | Voice counts plus enrichment/acoustic/embedding coverage |
| `run_voice_audition` | Run a full use-case audition with scorecard |
| `calculate_voice_costs` | Compare API vs self-hosted costs at volume |
| `find_similar_voices` | Find acoustically similar voices from stored embeddings |
| `get_acoustic_profile` | Return measured acoustic features for a voice |

## How it works

```
voice-audition search "warm female for healthcare"
    |
1. `catalog/voice_catalog.db` stores canonical voice/catalog state
    |
2. Query embedded into Moss (moss-minilm model) when credentials exist
    |
3. If Moss is unavailable, CLI falls back to SQLite keyword search
    |
4. Metadata filters applied and top-k results returned
```

Project-local state lives in `.voice-audition/` by default:

- `catalog/voice_catalog.db` for checked-in catalog data
- `.voice-audition/runtime.db` for local runtime state and query cache
- `.voice-audition/clips/` for human-audition audio clips

## Voice catalog

697 voices across 9 providers:

| Type | Providers |
|------|-----------|
| **Commercial** | ElevenLabs, OpenAI, Deepgram, Rime, Cartesia, PlayHT |
| **Open source** | Kokoro, Piper, Orpheus, Chatterbox, Fish Speech |

- Diff-based sync with lifecycle tracking (new/deprecated/changed detection)
- SQLite is the only catalog format; the checked-in catalog DB is the source of truth
- Weekly pricing change detection via page hash diff
- Research-backed schema: 8 perceptual traits, texture, pitch, emotional range
- Synced every 6 hours via GitHub Actions
- Provider reliability monitoring via status pages
- Open source registry includes hosting platform data (GPU requirements, inference speed)

## Enrichment pipeline

Most providers ship voice metadata. Rime is still the biggest enrichment gap. The enrichment pipeline classifies audio samples with Qwen2-Audio to fill in traits and descriptions, persists state in SQLite, and updates the checked-in catalog DB.

```bash
pip install voice-audition[enrich]
voice-audition enrich rime --limit 10
voice-audition enrich rime --yes
```

Additional derived-data passes:

```bash
voice-audition enrich-acoustic
voice-audition embed
```

## Audition profiles

5 built-in use-case profiles with role-specific scoring criteria:

- **Healthcare**: patient comfort, trust, empathy, clarity, pacing, sensitivity
- **Sales**: energy, rapport, persuasiveness, confidence, resilience, likability
- **Support**: patience, clarity, helpfulness, professionalism, warmth, resolution focus
- **Finance**: authority, precision, trustworthiness, calm, professionalism, compliance
- **Meditation**: calm, spaciousness, grounding, non-intrusive, breath quality, presence

## Self-hosting

Open source voices (Kokoro, Piper, Orpheus) run locally with no API costs. The catalog tracks GPU requirements and inference speed for each. Use `voice-audition costs <minutes>` to see when self-hosting beats API pricing for your volume.

## Development

```bash
git clone https://github.com/mnvsk97/voice-audition.git
cd voice-audition
pip install -e ".[mcp]"
```

## License

MIT
