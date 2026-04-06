import click


@click.group()
def main():
    """VoiceAudition — the casting director for your AI voice agent."""
    pass


@main.command()
@click.argument("providers", nargs=-1)
def sync(providers):
    """Sync voices from TTS providers."""
    from enrichment.sync import run_sync
    run_sync(list(providers) or None)


@main.command()
@click.argument("providers", nargs=-1)
@click.option("--retry", is_flag=True, help="Retry previously failed voices")
@click.option("--status", "show_status", is_flag=True, help="Show enrichment status summary")
def enrich(providers, retry, show_status):
    """Enrich voices with descriptions and traits. Configure in enrichment/enrichment.yaml."""
    if show_status:
        from enrichment.pipeline import load_catalog, CATALOG_DIR
        skip = {"providers", "hosting"}
        for f in sorted(CATALOG_DIR.glob("*.json")):
            if f.stem in skip:
                continue
            voices = load_catalog(f.stem) or []
            completed = sum(1 for v in voices if v.get("enrichment_status") == "completed")
            failed = sum(1 for v in voices if (v.get("enrichment_status") or "").startswith("failed:"))
            pending = len(voices) - completed - failed
            print(f"  {f.stem:<15} {len(voices):>4} total  {completed:>4} done  {failed:>4} failed  {pending:>4} pending")
        return
    from enrichment.pipeline import run_enrich
    try:
        run_enrich(list(providers) or None, retry=retry)
    except (ValueError, FileNotFoundError, ConnectionError, ImportError) as e:
        raise click.ClickException(str(e))


@main.command()
def monitor():
    """Check provider reliability via status pages."""
    from monitor.status import run_monitor
    run_monitor()


@main.command()
def stats():
    """Show catalog statistics."""
    from audition.search import show_stats
    show_stats()


@main.command("index")
@click.option("--force", is_flag=True, help="Rebuild index even if it exists")
def index_cmd(force):
    """Build or rebuild the Moss semantic search index."""
    from audition.index import run_index
    run_index(force=force)


@main.command()
@click.argument("query")
@click.option("--top-k", default=5, help="Number of results")
def search(query, top_k):
    """Semantic search the voice catalog."""
    from audition.index import run_semantic_search
    run_semantic_search(query, top_k=top_k)


@main.command()
@click.argument("brief")
@click.option("--candidates", default=8)
@click.option("--output", default=None)
@click.option("--gender", default=None)
@click.option("--provider", default=None)
def audition(brief, candidates, output, gender, provider):
    """Run a voice audition for a use case."""
    from audition.audition import run_audition
    run_audition(brief, num_candidates=candidates, output_dir=output, gender=gender, provider=provider)


@main.command()
def mcp():
    """Start the MCP server."""
    from mcp.server import run_mcp
    run_mcp()
