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
    result = run_sync(list(providers) or None)
    if result["errors"]:
        raise SystemExit(1)


@main.command()
@click.argument("providers", nargs=-1)
@click.option("--retry", is_flag=True, help="Retry previously failed voices")
@click.option("--limit", type=int, default=None, help="Limit voices per provider")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.option("--status", "show_status", is_flag=True, help="Show enrichment status summary")
def enrich(providers, retry, limit, yes, show_status):
    """Enrich voices with descriptions and traits."""
    if show_status:
        _print_enrich_status()
        return
    from enrichment.pipeline import run_enrich
    try:
        run_enrich(list(providers) or None, retry=retry, limit=limit, yes=yes)
    except (ValueError, FileNotFoundError, ConnectionError, ImportError) as e:
        raise click.ClickException(str(e))


@main.command()
@click.option("--retry", is_flag=True, help="Retry previously failed enrichments")
@click.option("--providers", "-p", multiple=True, help="Limit sync/enrich to specific providers")
def pipeline(retry, providers):
    """Run full pipeline: sync -> enrich new voices -> update index."""
    import time
    from datetime import datetime, timezone

    start = time.monotonic()
    ts = datetime.now(timezone.utc).isoformat()
    run = {"timestamp": ts, "steps": {}, "errors": []}
    provider_list = list(providers) or None

    # Step 1: Sync
    print("=" * 50)
    print("[pipeline] Step 1: Sync")
    print("=" * 50)
    try:
        from enrichment.sync import run_sync
        sync_result = run_sync(provider_list)
        run["steps"]["sync"] = sync_result
        if sync_result["errors"]:
            run["errors"].extend(f"sync:{e['provider']}:{e['error']}" for e in sync_result["errors"])
    except Exception as e:
        run["steps"]["sync"] = {"error": str(e)}
        run["errors"].append(f"sync:{e}")

    # Step 2: Enrich
    print("\n" + "=" * 50)
    print("[pipeline] Step 2: Enrich")
    print("=" * 50)
    try:
        from enrichment.pipeline import run_enrich
        enrich_result = run_enrich(provider_list, retry=retry)
        run["steps"]["enrich"] = enrich_result
    except (ValueError, FileNotFoundError, ConnectionError, ImportError) as e:
        print(f"[pipeline] Enrich skipped: {e}")
        run["steps"]["enrich"] = {"skipped": str(e)}
    except Exception as e:
        run["steps"]["enrich"] = {"error": str(e)}
        run["errors"].append(f"enrich:{e}")

    run["duration_s"] = round(time.monotonic() - start, 1)
    run["status"] = "ok" if not run["errors"] else "errors"

    print("\n" + "=" * 50)
    print(f"[pipeline] Done in {run['duration_s']}s — {run['status']}")
    if run["errors"]:
        for err in run["errors"]:
            print(f"  ERROR: {err}")


@main.command()
@click.option("--last", default=5, help="Show last N runs")
def runs(last):
    """Show recent pipeline runs."""
    import sqlite3

    from audition.db import get_runtime_db_path, init_runtime_db

    db_path = init_runtime_db()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sync_rows = conn.execute(
            """
            SELECT provider, status, added_count, updated_count, removed_count, total_count, error, finished_at
            FROM provider_sync_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (last,),
        ).fetchall()
        pipeline_rows = conn.execute(
            """
            SELECT stage, provider, voice_id, status, details_json, finished_at
            FROM pipeline_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (last,),
        ).fetchall()
    finally:
        conn.close()

    if not sync_rows and not pipeline_rows:
        print("No runs yet.")
        return

    if sync_rows:
        print("Recent sync runs:")
        for row in sync_rows:
            print(
                f"  {row['finished_at'] or '?'} {row['provider']} "
                f"+{row['added_count']} ~{row['updated_count']} -{row['removed_count']} "
                f"total={row['total_count']} [{row['status']}]"
            )
            if row["error"]:
                print(f"    ERROR: {row['error']}")

    if pipeline_rows:
        print("\nRecent pipeline events:")
        for row in pipeline_rows:
            label = row["voice_id"] or row["provider"] or "-"
            print(f"  {row['finished_at'] or '?'} {row['stage']} {label} [{row['status']}]")


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


@main.command()
@click.argument("minutes_per_month", type=int)
def costs(minutes_per_month):
    """Compare API vs self-hosted costs at a given monthly volume."""
    from audition.costs import calculate_voice_costs, render_voice_costs

    result = calculate_voice_costs(minutes_per_month)
    click.echo(render_voice_costs(result))


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


def _run_analyze_command(brief, candidates, gender, provider):
    from audition.analyze import analyze_brief

    filters = {}
    if gender:
        filters["gender"] = gender
    if provider:
        filters["provider"] = provider
    result = analyze_brief(brief, num_candidates=candidates, filters=filters)
    click.echo(f"[analyze] Use case: {result['use_case']}")
    click.echo(
        f"[analyze] Best overall: {result['best_overall']['name']} "
        f"({result['best_overall']['provider']}) cost={result['best_overall']['cost_per_min_usd']}"
    )
    click.echo(
        f"[analyze] Best budget: {result['best_budget']['name']} "
        f"({result['best_budget']['provider']}) cost={result['best_budget']['cost_per_min_usd']}"
    )
    click.echo(
        f"[analyze] Safest: {result['safest_option']['name']} "
        f"({result['safest_option']['provider']}) cost={result['safest_option']['cost_per_min_usd']}"
    )
    click.echo("[analyze] Shortlist:")
    for item in result["shortlist"]:
        click.echo(
            f"  {item['name']} ({item['provider']}) score={item['score']:.3f} "
            f"cost={item['cost_per_min_usd']} latency={item['latency_tier']}"
        )
    click.echo(f"[analyze] Analysis id: {result['analysis_id']}")
    click.echo(f"[analyze] Next: {result['next_step']}")


@main.command("analyze")
@click.argument("brief")
@click.option("--candidates", default=8)
@click.option("--gender", default=None)
@click.option("--provider", default=None)
def analyze_cmd(brief, candidates, gender, provider):
    """Analyze the best voice options without generating audio."""
    _run_analyze_command(brief, candidates, gender, provider)


@main.command("analyse")
@click.argument("brief")
@click.option("--candidates", default=8)
@click.option("--gender", default=None)
@click.option("--provider", default=None)
def analyse_cmd(brief, candidates, gender, provider):
    """Alias for analyze."""
    _run_analyze_command(brief, candidates, gender, provider)


@main.command("enrich-acoustic")
@click.argument("providers", nargs=-1)
def enrich_acoustic_cmd(providers):
    """Compute acoustic measurements for voices and store them in SQLite."""
    from audition.acoustic import enrich_acoustic

    result = enrich_acoustic(list(providers) or None)
    click.echo(f"Processed {result['processed']} voices; {result['failed']} failed.")


@main.command("score-quality")
@click.argument("providers", nargs=-1)
def score_quality_cmd(providers):
    """Compute UTMOS quality scores for voices with preview audio."""
    from audition.quality import score_voices

    result = score_voices(list(providers) or None)
    click.echo(
        f"Scored {result['processed']} voices; "
        f"{result['failed']} failed; {result['skipped']} already scored."
    )


@main.command("seed-elo")
def seed_elo_cmd():
    """Seed provider quality ELO scores from Artificial Analysis TTS Arena."""
    from audition.db import seed_provider_elo

    updated = seed_provider_elo()
    click.echo(f"Updated {updated} provider ELO scores.")


@main.command("embed")
@click.argument("providers", nargs=-1)
def embed_cmd(providers):
    """Generate CLAP embeddings for voices and store them in SQLite."""
    from audition.embeddings import embed_voices

    result = embed_voices(list(providers) or None)
    click.echo(f"Processed {result['processed']} voices; {result['failed']} failed.")


@main.command("search-audio")
@click.argument("path")
@click.option("--top-k", default=5, help="Number of results")
def search_audio_cmd(path, top_k):
    """Find voices acoustically similar to an audio file."""
    from audition.embeddings import search_audio

    results = search_audio(path, top_k=top_k)
    click.echo(f'Audio search: "{path}" ({len(results)} results)\n')
    for row in results:
        click.echo(
            f"  {row.get('score', 0):.3f}  {row.get('name', '')} "
            f"({row.get('provider', '')}) [{row.get('gender', '')}]"
        )


@main.command()
@click.argument("brief")
@click.option("--candidates", default=8)
@click.option("--output", default=None)
@click.option("--gender", default=None)
@click.option("--provider", default=None)
@click.option("--mode", type=click.Choice(["ai", "human"]), default="ai")
def audition(brief, candidates, output, gender, provider, mode):
    """Run a voice audition for a use case."""
    from audition.audition import run_audition
    run_audition(brief, num_candidates=candidates, output_dir=output, gender=gender, provider=provider, mode=mode)


@main.command()
def mcp():
    """Start the MCP server."""
    from mcp.server import run_mcp
    run_mcp()


def _print_enrich_status():
    from audition.db import list_providers, load_voices

    for provider in list_providers():
        voices = load_voices(provider=provider) or []
        completed = sum(1 for v in voices if v.get("enrichment_status") == "completed")
        failed = sum(1 for v in voices if (v.get("enrichment_status") or "").startswith("failed:"))
        pending = len(voices) - completed - failed
        print(f"  {provider:<15} {len(voices):>4} total  {completed:>4} done  {failed:>4} failed  {pending:>4} pending")
