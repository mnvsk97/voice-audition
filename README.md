# voice-audition

[![PyPI](https://img.shields.io/pypi/v/voice-audition)](https://pypi.org/project/voice-audition/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

The casting director for your AI voice agent. 697 voices across 9 TTS providers (645 enriched with LLM-generated descriptions and traits), semantic search via Moss, use-case auditions with AI scoring, cost comparison, web UI, and MCP server for Claude.

## Install

```bash
pip install voice-audition
pip install voice-audition[enrich]   # LLM-based voice enrichment (Gemini, OpenAI, local MLX)
pip install voice-audition[mcp]      # MCP server for Claude Desktop
pip install voice-audition[acoustic] # acoustic feature analysis (librosa, Parselmouth)
pip install voice-audition[clap]     # CLAP embeddings for audio similarity search
```

## Setup

```bash
cp .env.example .env
# Fill in the API keys you need (all optional)
```

Provider API keys are optional — you only need keys for the providers you want to sync. Moss credentials enable semantic search; without them, keyword search is used as fallback.

## Quick start

```bash
# Sync voices from providers
voice-audition sync

# Search
voice-audition search "warm female voice for healthcare"

# Analyze top options (no audio generated)
voice-audition analyze "voice for fertility clinic"

# Run a full audition with AI scoring
voice-audition audition "fertility clinic for anxious IVF patients" --gender female

# Compare costs at scale
voice-audition costs 100000
```

## Web UI

A lightweight web interface for browsing the voice catalog, filtering by attributes, and generating TTS audio samples.

```bash
# Terminal 1: Start the Hono API server
cd server && npm install && npm run dev

# Terminal 2: Start the Vite frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:5173. The UI provides:
- Voice list with search and filters (provider, gender, age, texture, pitch, use case, enrichment status)
- Voice detail pages with trait scores, tags, and descriptions
- TTS generation — type text and hear any voice (requires provider API keys in `.env`)

## Commands

| Command | What it does |
|---------|-------------|
| `voice-audition sync [providers...]` | Sync voices from TTS provider APIs |
| `voice-audition enrich [providers...] [--status]` | Enrich voices with LLM-generated descriptions and traits |
| `voice-audition pipeline [--providers ...]` | Run full pipeline: sync → enrich → rebuild index |
| `voice-audition index [--force]` | Build or rebuild the Moss semantic search index |
| `voice-audition search <query> [--top-k N]` | Semantic search (falls back to keyword search without Moss) |
| `voice-audition analyze <brief>` | Recommend best/budget/safest voices without generating audio |
| `voice-audition audition <brief> [--mode ai\|human]` | Run a use-case audition with audio generation and scoring |
| `voice-audition costs <minutes>` | Compare API vs self-hosted costs at a monthly volume |
| `voice-audition enrich-acoustic [providers...]` | Extract acoustic features (pitch, speech rate, HNR) |
| `voice-audition embed [providers...]` | Generate CLAP embeddings for audio similarity |
| `voice-audition search-audio <path>` | Find voices similar to an audio clip |
| `voice-audition stats` | Catalog statistics |
| `voice-audition runs [--last N]` | Recent pipeline run history |
| `voice-audition monitor` | Check provider reliability via status pages |
| `voice-audition mcp` | Start the MCP server |

## MCP server

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

| Tool | What it does |
|------|-------------|
| `search_voices` | Semantic search with optional acoustic filters |
| `analyze_voices` | Recommend best voices without generating audio |
| `filter_voices` | Filter by gender, provider, accent, age group, use case |
| `get_voice` | Full details for a specific voice |
| `get_catalog_stats` | Catalog overview with enrichment coverage |
| `run_voice_audition` | Full audition with audio generation and AI scoring |
| `calculate_voice_costs` | API vs self-hosted cost comparison |
| `find_similar_voices` | Find acoustically similar voices via embeddings |
| `get_acoustic_profile` | Measured acoustic features for a voice |

## Voice catalog

697 voices across 9 providers in a checked-in SQLite database (645 enriched):

| Type | Providers |
|------|-----------|
| **Commercial** | ElevenLabs, OpenAI, Deepgram, Rime |
| **Syncable** | Cartesia, PlayHT, Azure, Google (API keys required) |
| **Open source** | Kokoro, Piper, Orpheus, Chatterbox, Fish Speech |

- Diff-based sync: detects added, removed, and changed voices
- Enrichment data preserved across re-syncs
- Deprecated voices filtered from search/audition
- Weekly pricing change detection via page hash diff
- Rich failure metadata with error classification (transient/auth/unsupported/validation)

## Enrichment

The enrichment pipeline generates audio samples, sends them to an LLM for classification, and fills in descriptions, traits, and tags. Configure your LLM provider in `enrichment/enrichment.yaml`:

```yaml
enrichment:
  provider: gemini  # gemini | openai | anthropic | ollama | mlx
```

Supported: Gemini, OpenAI, Anthropic, Bedrock, Ollama (Qwen2-Audio), local MLX.

TTS generators for enrichment audio: Rime, ElevenLabs, Deepgram, OpenAI. Open-source models (Kokoro, Piper) supported with local setup.

```bash
voice-audition enrich rime --limit 10    # enrich 10 Rime voices
voice-audition enrich --status           # show enrichment progress
voice-audition enrich --retry            # retry failed voices (up to 3 attempts)
voice-audition pipeline                  # sync + enrich + rebuild index
```

## Audition profiles

6 built-in use-case profiles with domain-specific scoring criteria:

| Profile | Criteria |
|---------|----------|
| Healthcare | patient comfort, trust, empathy, clarity, pacing, sensitivity |
| Sales | energy, rapport, persuasiveness, confidence, resilience, likability |
| Support | patience, clarity, helpfulness, professionalism, warmth, resolution focus |
| Finance | authority, precision, trustworthiness, calm, professionalism, compliance |
| Meditation | calm, spaciousness, grounding, non-intrusive, breath quality, presence |
| Education | clarity, patience, encouragement, structure, warmth, confidence |

## Development

```bash
git clone https://github.com/mnvsk97/voice-audition.git
cd voice-audition
pip install -e ".[mcp,enrich]"
python -m pytest tests/
```

## License

MIT
