"""CLI for journey-map-generator — CPR Orbital Tool #38."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .engine import scaffold_journey_map
from .export import emotion_arc_text, to_csv, to_json, to_markdown
from .models import JourneyMap

console = Console()


def _load_input(path: Optional[str], stdin_data: Optional[str]) -> str:
    """Load raw research data from file or stdin."""
    if path:
        p = Path(path)
        if not p.exists():
            console.print(f"[red]Error:[/red] File not found: {path}")
            sys.exit(1)
        return p.read_text(encoding="utf-8")
    if stdin_data:
        return stdin_data
    # Try stdin
    if not sys.stdin.isatty():
        return sys.stdin.read()
    console.print("[red]Error:[/red] Provide input via --input or stdin.")
    sys.exit(1)


def _apply_llm(journey: JourneyMap, backend: str, raw_data: str) -> JourneyMap:
    """Apply LLM enrichment, handling import errors gracefully."""
    try:
        from .llm import enrich_journey_map
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Enriching with {backend}…", total=None)
            result = enrich_journey_map(journey, raw_data, backend=backend)
            progress.update(task, completed=True)
        return result
    except ImportError:
        console.print(
            "[yellow]Warning:[/yellow] LLM enrichment requires litellm. "
            "Install with: pip install 'journey-map-generator[llm]'\n"
            "Falling back to rule-based output."
        )
        return journey
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] LLM enrichment failed: {e}")
        return journey


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

@click.group()
@click.version_option()
def cli():
    """
    journey-map-generator — CPR Orbital Tool #38

    Scaffold journey maps with phases, pain points, and emotions
    from coded research data. LLM enrichment optional via --llm-backend.
    """


@cli.command()
@click.option("--input", "-i", "input_path", default=None, help="Path to coded research data file")
@click.option("--persona", "-p", default="Primary User", help="Persona name")
@click.option("--persona-role", default=None, help="Persona role/description")
@click.option("--title", "-t", default=None, help="Journey map title")
@click.option(
    "--llm-backend",
    default="claude",
    show_default=True,
    type=click.Choice(["claude", "gemini", "openai", "none"], case_sensitive=False),
    help="LLM backend for enrichment (default: claude). Use 'none' for rule-based only.",
)
@click.option("--output", "-o", default=None, help="Output file path (default: stdout)")
@click.option(
    "--format", "-f", "fmt",
    default="rich",
    type=click.Choice(["rich", "json", "markdown", "csv"], case_sensitive=False),
    help="Output format",
)
@click.option("--no-arc", is_flag=True, default=False, help="Skip emotion arc display")
def generate(
    input_path, persona, persona_role, title, llm_backend, output, fmt, no_arc
):
    """Generate a journey map from coded research data."""
    raw_data = _load_input(input_path, None)

    if fmt != "json":
        console.print(Panel.fit(
            "[bold]journey-map-generator[/bold] · CPR Orbital #38",
            subtitle="Computational Product Research",
            border_style="blue",
        ))

    # Rule-based scaffold
    journey = scaffold_journey_map(
        raw_data=raw_data,
        persona_name=persona,
        persona_role=persona_role,
        title=title,
    )

    # LLM enrichment (on by default)
    if llm_backend.lower() != "none":
        journey = _apply_llm(journey, llm_backend, raw_data)

    # Output
    if fmt == "json":
        result = to_json(journey)
    elif fmt == "markdown":
        result = to_markdown(journey)
    elif fmt == "csv":
        result = to_csv(journey)
    else:
        result = None

    if result:
        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]✓[/green] Written to {output}")
        else:
            print(result)
        return

    # Rich terminal display
    _display_rich(journey, no_arc)

    if output:
        md = to_markdown(journey)
        Path(output).write_text(md, encoding="utf-8")
        console.print(f"\n[green]✓[/green] Journey map saved to {output}")


def _display_rich(journey: JourneyMap, no_arc: bool):
    """Display journey map in rich terminal format."""
    console.print(f"\n[bold blue]{journey.title}[/bold blue]")
    console.print(f"[dim]Persona: {journey.persona.name}[/dim]")
    if journey.persona.role:
        console.print(f"[dim]Role: {journey.persona.role}[/dim]")
    console.print()

    if journey.summary:
        console.print(Panel(journey.summary, title="[bold]Journey Summary[/bold]", border_style="blue"))
        console.print()

    if journey.key_insights:
        console.print("[bold yellow]Key Insights[/bold yellow]")
        for i, ins in enumerate(journey.key_insights, 1):
            console.print(f"  {i}. {ins}")
        console.print()

    if journey.critical_moments:
        console.print("[bold red]Moments of Truth[/bold red]")
        for i, m in enumerate(journey.critical_moments, 1):
            console.print(f"  {i}. {m}")
        console.print()

    for ph in journey.phases:
        sentiment = ph.overall_sentiment
        sentiment_icon = "🟢" if sentiment > 0.2 else "🟡" if sentiment > -0.2 else "🔴"
        console.print(
            f"[bold]{sentiment_icon} {ph.name}[/bold]  "
            f"[dim]sentiment: {sentiment:+.2f}[/dim]"
        )

        for st in ph.steps:
            emotion_color = (
                "green" if st.emotion_score > 0.4
                else "yellow" if st.emotion_score > -0.2
                else "red"
            )
            console.print(
                f"  [dim]→[/dim] [{emotion_color}]{st.name[:60]}[/{emotion_color}]"
                f"  [dim]{st.emotion.value}[/dim]"
            )
            for pp in st.pain_points:
                sev_color = {"critical": "red", "moderate": "yellow", "minor": "dim"}[pp.severity.value]
                console.print(f"    [bold {sev_color}][{pp.severity.value.upper()}][/bold {sev_color}] {pp.description[:80]}")
            for opp in st.opportunities:
                console.print(f"    [blue]💡[/blue] {opp.description[:80]}")
        console.print()

    if not no_arc:
        console.print("[bold]Emotion Arc[/bold]")
        console.print(emotion_arc_text(journey))
        console.print()

    if journey.source_data_summary:
        console.print(f"[dim]{journey.source_data_summary}[/dim]")
    if journey.llm_backend:
        console.print(f"[dim]LLM: {journey.llm_backend}[/dim]")


@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Path to research data file")
@click.option("--personas", "-p", default="Primary User", help="Comma-separated persona names")
@click.option(
    "--llm-backend",
    default="claude",
    type=click.Choice(["claude", "gemini", "openai", "none"], case_sensitive=False),
)
@click.option("--output-dir", "-d", default=".", help="Output directory for generated maps")
def batch(input_path, personas, llm_backend, output_dir):
    """Generate journey maps for multiple personas from one dataset."""
    raw_data = _load_input(input_path, None)
    persona_list = [p.strip() for p in personas.split(",")]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        f"[bold]Batch mode[/bold] — {len(persona_list)} persona(s)",
        border_style="blue",
    ))

    for persona_name in persona_list:
        console.print(f"\n[bold]Processing: {persona_name}[/bold]")
        journey = scaffold_journey_map(raw_data=raw_data, persona_name=persona_name)
        if llm_backend.lower() != "none":
            journey = _apply_llm(journey, llm_backend, raw_data)

        slug = persona_name.lower().replace(" ", "-")
        md_path = out_dir / f"journey-{slug}.md"
        json_path = out_dir / f"journey-{slug}.json"

        md_path.write_text(to_markdown(journey), encoding="utf-8")
        json_path.write_text(to_json(journey), encoding="utf-8")
        console.print(f"  [green]✓[/green] {md_path}")
        console.print(f"  [green]✓[/green] {json_path}")

    console.print(f"\n[green]Done.[/green] {len(persona_list)} map(s) written to {output_dir}")


if __name__ == "__main__":
    cli()
