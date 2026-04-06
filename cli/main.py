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
@click.option("--status", "show_status", is_flag=True, help="Show enrichment status summary")
def enrich(providers, retry, show_status):
    """Enrich voices with descriptions and traits."""
    if show_status:
        _print_enrich_status()
        return
    from enrichment.pipeline import run_enrich
    try:
        run_enrich(list(providers) or None, retry=retry)
    except (ValueError, FileNotFoundError, ConnectionError, ImportError) as e:
        raise click.ClickException(str(e))


@main.command()
@click.option("--retry", is_flag=True, help="Retry previously failed enrichments")
@click.option("--providers", "-p", multiple=True, help="Limit sync/enrich to specific providers")
def pipeline(retry, providers):
    """Run full pipeline: sync -> enrich new voices -> update index."""
    import json
    import time
    from datetime import datetime, timezone
    from pathlib import Path

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

    # Append to run log
    log_path = Path(__file__).resolve().parent.parent / "runs.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(run) + "\n")

    print("\n" + "=" * 50)
    print(f"[pipeline] Done in {run['duration_s']}s — {run['status']}")
    if run["errors"]:
        for err in run["errors"]:
            print(f"  ERROR: {err}")
    print(f"[pipeline] Run log: {log_path}")


@main.command()
@click.option("--last", default=5, help="Show last N runs")
def runs(last):
    """Show recent pipeline runs."""
    import json
    from pathlib import Path

    log_path = Path(__file__).resolve().parent.parent / "runs.jsonl"
    if not log_path.exists():
        print("No runs yet.")
        return
    lines = log_path.read_text().strip().split("\n")
    for line in lines[-last:]:
        r = json.loads(line)
        sync_info = r.get("steps", {}).get("sync", {})
        enrich_info = r.get("steps", {}).get("enrich", {})
        synced_count = sum(s.get("added", 0) for s in sync_info.get("synced", []))
        enriched_count = enrich_info.get("enriched", 0)
        failed_count = enrich_info.get("failed", 0)
        print(f"  {r['timestamp'][:19]}  {r.get('duration_s', '?')}s  "
              f"+{synced_count} synced  +{enriched_count} enriched  {failed_count} failed  "
              f"[{r.get('status', '?')}]")
        for err in r.get("errors", []):
            print(f"    ERROR: {err}")


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


def _print_enrich_status():
    from enrichment.pipeline import load_catalog
    from enrichment import CATALOG_DIR
    skip = {"providers", "hosting"}
    for f in sorted(CATALOG_DIR.glob("*.json")):
        if f.stem in skip:
            continue
        voices = load_catalog(f.stem) or []
        completed = sum(1 for v in voices if v.get("enrichment_status") == "completed")
        failed = sum(1 for v in voices if (v.get("enrichment_status") or "").startswith("failed:"))
        pending = len(voices) - completed - failed
        print(f"  {f.stem:<15} {len(voices):>4} total  {completed:>4} done  {failed:>4} failed  {pending:>4} pending")
