"""
Interactive CLI for voice selection.
Walks users through a guided interview to find their ideal voice.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm

from .models import (
    AgeRange, BrandPersonality, CostTier, Gender, LatencyTier,
    Provider, Requirements, UseCase,
)
from .engine import suggest

app = typer.Typer(help="VoiceAudition — audition TTS voices for your AI agent.")
console = Console()


def _pick_enum(prompt_text: str, enum_cls: type, allow_none: bool = False) -> str | None:
    options = [e.value for e in enum_cls]
    display = ", ".join(options)
    if allow_none:
        display += ", none"
    console.print(f"\n[bold]{prompt_text}[/bold]")
    console.print(f"  Options: [dim]{display}[/dim]")
    while True:
        choice = Prompt.ask("  Choice").strip().lower()
        if allow_none and choice in ("none", ""):
            return None
        if choice in options:
            return choice
        console.print(f"  [red]Invalid. Pick from: {display}[/red]")


def _pick_multi_enum(prompt_text: str, enum_cls: type) -> list[str]:
    options = [e.value for e in enum_cls]
    display = ", ".join(options)
    console.print(f"\n[bold]{prompt_text}[/bold]")
    console.print(f"  Options: [dim]{display}[/dim]")
    console.print("  [dim]Comma-separated, e.g.: friendly, empathetic[/dim]")
    while True:
        raw = Prompt.ask("  Choice").strip().lower()
        picks = [p.strip() for p in raw.split(",") if p.strip()]
        if all(p in options for p in picks) and picks:
            return picks
        console.print(f"  [red]Invalid. Pick from: {display}[/red]")


def _display_results(results):
    if not results:
        console.print("\n[red]No voices match your requirements. Try relaxing constraints.[/red]")
        return

    console.print(f"\n[bold green]Top {len(results)} Voice Recommendations[/bold green]\n")

    for i, sv in enumerate(results, 1):
        v = sv.voice
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold cyan", width=14)
        table.add_column()
        table.add_row("Provider", f"{v.provider.value}")
        table.add_row("Voice ID", f"{v.provider_voice_id}")
        table.add_row("Gender/Age", f"{v.gender.value} / {v.age_range.value}")
        table.add_row("Accent", v.accent)
        table.add_row("Latency", v.latency_tier.value)
        table.add_row("Cost", v.cost_tier.value)
        table.add_row("Best For", ", ".join(u.value for u in v.best_for))

        breakdown_str = " | ".join(f"{k}: {val}" for k, val in sv.breakdown.items())
        table.add_row("Score", f"[bold]{sv.score}/100[/bold]  ({breakdown_str})")

        console.print(Panel(
            table,
            title=f"[bold]#{i} {v.name}[/bold] - {v.description}",
            border_style="green" if i == 1 else "blue",
        ))

    # Show Pipecat config for top pick
    top = results[0]
    console.print(f"\n[bold]Pipecat config for top pick ({top.voice.name}):[/bold]")
    console.print(Syntax(top.pipecat_config, "python", theme="monokai"))


@app.command()
def interview():
    """Guided interview to find your ideal voice agent voice."""
    console.print(Panel(
        "[bold]VoiceAudition[/bold]\n"
        "Answer a few questions and I'll audition the best TTS voices\n"
        "for your voice agent, with a ready-to-use Pipecat config.",
        border_style="cyan",
    ))

    use_case = _pick_enum("What's the primary use case?", UseCase)
    personalities = _pick_multi_enum("What brand personality should the voice convey?", BrandPersonality)
    gender = _pick_enum("Gender preference?", Gender, allow_none=True)
    age = _pick_enum("Age range preference?", AgeRange, allow_none=True)
    accent = Prompt.ask("\n[bold]Accent preference?[/bold] (american, british, or leave blank)", default="").strip() or None
    latency = _pick_enum("Maximum acceptable latency tier?", LatencyTier)
    cost = _pick_enum("Maximum cost tier?", CostTier)
    provider = _pick_enum("Prefer a specific provider?", Provider, allow_none=True)

    req = Requirements(
        use_case=UseCase(use_case),
        brand_personality=[BrandPersonality(p) for p in personalities],
        gender_preference=Gender(gender) if gender else None,
        age_preference=AgeRange(age) if age else None,
        accent=accent,
        max_latency=LatencyTier(latency),
        max_cost=CostTier(cost),
        provider_preference=Provider(provider) if provider else None,
    )

    results = suggest(req, top_n=5)
    _display_results(results)

    if results and Confirm.ask("\n[bold]Show Pipecat config for all recommendations?[/bold]"):
        for sv in results:
            console.print(f"\n[bold cyan]{sv.voice.name} ({sv.voice.provider.value}):[/bold cyan]")
            console.print(Syntax(sv.pipecat_config, "python", theme="monokai"))


@app.command()
def quick(
    use_case: str = typer.Argument(help="Use case (e.g. healthcare, sales)"),
    personality: str = typer.Option("professional", help="Comma-separated brand personalities"),
    gender: str = typer.Option(None, help="male, female, or neutral"),
    latency: str = typer.Option("fast", help="fastest, fast, or standard"),
    cost: str = typer.Option("medium", help="low, medium, or high"),
    provider: str = typer.Option(None, help="Specific provider preference"),
    top: int = typer.Option(5, help="Number of results"),
):
    """Quick voice suggestion without the full interview."""
    req = Requirements(
        use_case=UseCase(use_case),
        brand_personality=[BrandPersonality(p.strip()) for p in personality.split(",")],
        gender_preference=Gender(gender) if gender else None,
        max_latency=LatencyTier(latency),
        max_cost=CostTier(cost),
        provider_preference=Provider(provider) if provider else None,
    )
    results = suggest(req, top_n=top)
    _display_results(results)


@app.command()
def providers():
    """List all supported TTS providers and their characteristics."""
    table = Table(title="TTS Providers for Voice Agents")
    table.add_column("Provider", style="cyan bold")
    table.add_column("Latency")
    table.add_column("Cost")
    table.add_column("Quality")
    table.add_column("Best For")

    rows = [
        ("Cartesia", "Fastest (<150ms)", "Medium", "Very Good", "Speed-critical real-time agents"),
        ("ElevenLabs", "Fast (200-400ms)", "High", "Best", "Premium quality, emotional range"),
        ("Deepgram Aura", "Fastest (<100ms)", "Low", "Good", "High-volume, cost-sensitive"),
        ("OpenAI TTS", "Fast (200-500ms)", "Medium", "Very Good", "Easy integration, good quality"),
        ("PlayHT", "Fast (200-400ms)", "Medium", "Very Good", "Voice cloning, variety"),
        ("Rime", "Fastest (<100ms)", "Low", "Good", "Ultra-low latency deployments"),
        ("Azure", "Standard (300-600ms)", "Low", "Good", "Enterprise, multilingual"),
        ("Google", "Standard (300-600ms)", "Low", "Good", "Enterprise, multilingual"),
    ]
    for row in rows:
        table.add_row(*row)

    console.print(table)


@app.command()
def voices(
    provider: str = typer.Option(None, help="Filter by provider"),
    use_case: str = typer.Option(None, help="Filter by use case"),
):
    """Browse the voice catalog."""
    from .catalog import VOICES

    filtered = VOICES
    if provider:
        filtered = [v for v in filtered if v.provider.value == provider]
    if use_case:
        uc = UseCase(use_case)
        filtered = [v for v in filtered if uc in v.best_for]

    table = Table(title=f"Voice Catalog ({len(filtered)} voices)")
    table.add_column("Name", style="cyan bold")
    table.add_column("Provider")
    table.add_column("Gender")
    table.add_column("Latency")
    table.add_column("Cost")
    table.add_column("Description", max_width=50)

    for v in filtered:
        table.add_row(v.name, v.provider.value, v.gender.value, v.latency_tier.value, v.cost_tier.value, v.description)

    console.print(table)


if __name__ == "__main__":
    app()
