"""CLI entrypoint for voice-audition."""

import click


@click.group()
def main():
    """VoiceAudition — the casting director for your AI voice agent."""
    pass


@main.command()
@click.argument("providers", nargs=-1)
def sync(providers):
    """Sync voices from TTS providers."""
    from voice_audition.sync import run_sync
    run_sync(list(providers) or None)


@main.command()
@click.argument("providers", nargs=-1)
@click.option("--model", default="qwen2-audio", help="Classification model")
def enrich(providers, model):
    """Enrich unenriched voices with descriptions and traits."""
    from voice_audition.enrich import run_enrich
    run_enrich(list(providers) or None, model=model)


@main.command()
def monitor():
    """Check provider reliability via status pages."""
    from voice_audition.monitor import run_monitor
    run_monitor()


@main.command()
@click.argument("query", required=False)
def stats(query):
    """Show catalog statistics."""
    from voice_audition.search import show_stats
    show_stats()


@main.command()
@click.argument("query")
def search(query):
    """Search the voice catalog."""
    from voice_audition.search import run_search
    run_search(query)
