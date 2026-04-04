# voice-audition

The casting director for your AI voice agent. Search 697 voices across 9 TTS providers with semantic search, run use-case auditions, and compare API vs self-hosted costs.

## Install

```bash
pip install voice-audition
pip install voice-audition[enrich]   # adds Qwen2-Audio enrichment
pip install voice-audition[mcp]      # adds MCP server for Claude
```

## Setup

```bash
cp .env.example .env
```

```bash
# Required: Moss credentials for semantic search
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
```

## Quick start

```bash
# Sync voices from all providers
voice-audition sync

# Build search index
voice-audition index

# Search
voice-audition search "warm female voice for healthcare"

# Run a full audition
voice-audition audition "fertility clinic for anxious IVF patients" --gender female

# Compare costs at 100k minutes/month
voice-audition costs 100000
```

## Commands

| Command | What it does |
|---------|-------------|
| `voice-audition sync [providers...]` | Sync voices from TTS providers with diff-based lifecycle tracking |
| `voice-audition index` | Build or rebuild the Moss semantic search index |
| `voice-audition search <query>` | Semantic search the voice catalog (`--top-k` for result count) |
| `voice-audition enrich [providers...]` | Enrich voices with Qwen2-Audio descriptions and traits (`--model`) |
| `voice-audition audition <brief>` | Run a use-case audition with ranked scorecard (`--candidates`, `--gender`, `--provider`) |
| `voice-audition costs <minutes>` | Compare API vs self-hosted costs at a given monthly volume |
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

Exposes 7 tools:

| Tool | What it does |
|------|-------------|
| `search_voices` | Semantic search across the full catalog |
| `get_voice` | Get detailed info for a specific voice |
| `filter_voices` | Filter by gender, provider, cost, latency |
| `get_providers` | List available TTS providers and status |
| `get_catalog_stats` | Voice counts, coverage, freshness |
| `run_voice_audition` | Run a full use-case audition with scorecard |
| `calculate_voice_costs` | Compare API vs self-hosted costs at volume |

## How it works

```
voice-audition search "warm female for healthcare"
    |
1. Query embedded (Moss, moss-minilm model)
    |
2. Hybrid search: semantic similarity + keyword matching (alpha=0.7)
   Name-based vibes fill in for unenriched voices
    |
3. Metadata filters applied (gender, provider, cost, latency)
    |
4. Top-k results ranked by relevance score
```

## Voice catalog

697 voices across 9 providers:

| Type | Providers |
|------|-----------|
| **Commercial** | ElevenLabs, OpenAI, Deepgram, Rime, Cartesia, PlayHT |
| **Open source** | Kokoro, Piper, Orpheus, Chatterbox, Fish Speech |

- Diff-based sync with lifecycle tracking (new/deprecated/changed detection)
- Weekly pricing change detection via page hash diff
- Research-backed schema: 8 perceptual traits, texture, pitch, emotional range
- Synced every 6 hours via GitHub Actions
- Provider reliability monitoring via status pages
- Open source registry includes hosting platform data (GPU requirements, inference speed)

## Enrichment pipeline

Most providers ship voice metadata. Rime does not -- its 610 voices have no descriptions. The enrichment pipeline classifies audio samples with Qwen2-Audio to fill in traits and descriptions. Tested on 10 voices.

```bash
pip install voice-audition[enrich]
voice-audition enrich rime --model qwen2-audio
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

## Research

See the `research/` directory. Key findings:

- Voice perception collapses to 2 axes: warmth vs authority (McAleer et al.)
- Speech rate is the #1 trust predictor, not pitch
- Emotional voices: +50% CSAT but -20% accuracy (Deepgram)

## Development

```bash
git clone https://github.com/mnvsk97/voice-audition.git
cd voice-audition
pip install -e ".[mcp]"
```

## License

MIT
