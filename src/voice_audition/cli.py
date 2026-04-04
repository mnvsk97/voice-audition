import click


@click.group()
def main():
    """VoiceAudition — the casting director for your AI voice agent."""
    pass


@main.command()
@click.argument("providers", nargs=-1)
def sync(providers):
    """Sync voices from TTS providers."""
    from voice_audition.sync.providers import run_sync
    run_sync(list(providers) or None)


@main.command()
@click.argument("providers", nargs=-1)
@click.option("--model", default="qwen2-audio", help="Classification model")
def enrich(providers, model):
    """Enrich unenriched voices with descriptions and traits."""
    from voice_audition.enrich.pipeline import run_enrich
    run_enrich(list(providers) or None, model=model)


@main.command()
def monitor():
    """Check provider reliability via status pages."""
    from voice_audition.monitor.status import run_monitor
    run_monitor()


@main.command()
def stats():
    """Show catalog statistics."""
    from voice_audition.search import show_stats
    show_stats()


@main.command("index")
@click.option("--force", is_flag=True, help="Rebuild index even if it exists")
def index_cmd(force):
    """Build or rebuild the Moss semantic search index."""
    from voice_audition.index import run_index
    run_index(force=force)


@main.command()
@click.argument("query")
@click.option("--top-k", default=5, help="Number of results")
def search(query, top_k):
    """Semantic search the voice catalog."""
    from voice_audition.index import run_semantic_search
    run_semantic_search(query, top_k=top_k)


@main.command()
@click.argument("brief")
@click.option("--candidates", default=8, help="Number of candidates to audition")
@click.option("--output", default=None, help="Output directory for audio + scorecard")
@click.option("--gender", default=None, help="Filter by gender")
@click.option("--provider", default=None, help="Filter by provider")
def audition(brief, candidates, output, gender, provider):
    """Run a voice audition for a use case.

    Example: voice-audition audition "fertility clinic for anxious IVF patients"
    """
    from voice_audition.audition import run_audition
    run_audition(brief, num_candidates=candidates, output_dir=output, gender=gender, provider=provider)


@main.command()
@click.argument("minutes", type=int)
def costs(minutes):
    """Compare API vs self-hosted costs at a given volume.

    MINUTES is monthly minutes of TTS usage.
    Example: voice-audition costs 100000
    """
    from voice_audition.costs import run_costs
    run_costs(minutes)


@main.command()
def mcp():
    """Start the MCP server for Claude integration."""
    from voice_audition.mcp_server import run_mcp
    run_mcp()
