# voice-audition

The casting director for your AI voice agent. Search 670+ voices across 6 TTS providers with semantic search.

## Install

```bash
pip install voice-audition
```

## Setup

```bash
# Copy env template and fill in keys
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
voice-audition search "authoritative male British accent"

# Check catalog
voice-audition stats

# Monitor provider reliability
voice-audition monitor
```

## Commands

| Command | What it does |
|---------|-------------|
| `voice-audition sync [providers...]` | Sync voices from TTS providers (all if none specified) |
| `voice-audition index` | Build or rebuild the Moss semantic search index |
| `voice-audition search <query>` | Semantic search the voice catalog (`--top-k` for result count) |
| `voice-audition enrich [providers...]` | Enrich unenriched voices with descriptions and traits (`--model` to pick classifier) |
| `voice-audition monitor` | Check provider reliability via status pages |
| `voice-audition stats` | Show catalog statistics |
| `voice-audition mcp` | Start the MCP server for Claude integration |

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

Exposes 5 tools:

| Tool | What it does |
|------|-------------|
| `search_voices` | Semantic search across the full catalog |
| `get_voice` | Get detailed info for a specific voice |
| `filter_voices` | Filter by gender, provider, cost, latency |
| `get_providers` | List available TTS providers and status |
| `get_catalog_stats` | Voice counts, coverage, freshness |

## How it works

```
voice-audition search "warm female for healthcare"
    |
1. Query embedded (Moss, moss-minilm model)
    |
2. Hybrid search: semantic similarity + keyword matching (alpha=0.7)
    |
3. Metadata filters applied (gender, provider, cost, latency)
    |
4. Top-k results ranked by relevance score
```

## Voice catalog

- 670+ voices across 6 providers: ElevenLabs, OpenAI, Deepgram, Rime, Cartesia, PlayHT
- Research-backed schema: 8 perceptual traits, texture, pitch, emotional range
- Synced every 6 hours via GitHub Actions
- Provider reliability monitoring via status pages

## Enrichment pipeline

Most providers ship voice metadata. Rime does not -- its 610 voices have no descriptions. The enrichment pipeline generates audio samples and classifies them with a local model (Qwen2-Audio via `mlx-audio`) to fill in traits and descriptions.

```bash
pip install voice-audition[enrich]
voice-audition enrich rime --model qwen2-audio
```

The classifier is currently stubbed and needs implementation.

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
