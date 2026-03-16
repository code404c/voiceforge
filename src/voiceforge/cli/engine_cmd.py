"""Engine listing and inspection commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from voiceforge.engine import get_engine, list_engines
from voiceforge.engine.registry import _registry

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("list")
def engine_list() -> None:
    """Show all registered TTS engines."""
    infos = list_engines()
    if not infos:
        console.print("[yellow]No engines registered.[/yellow]")
        raise typer.Exit()

    table = Table(title="Registered Engines")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version")
    table.add_column("Description")

    for info in infos:
        table.add_row(info.name, info.version, info.description)

    console.print(table)


@app.command("info")
def engine_info(name: str = typer.Argument(..., help="Engine name")) -> None:
    """Show detailed information about a TTS engine."""
    if name not in _registry:
        available = ", ".join(sorted(_registry)) or "(none)"
        console.print(f"[red]Unknown engine '{name}'. Available: {available}[/red]")
        raise typer.Exit(code=1)

    eng = get_engine(name)
    info = eng.info()

    panel = Panel(
        f"[bold]Name:[/bold]        {info.name}\n"
        f"[bold]Version:[/bold]     {info.version}\n"
        f"[bold]Description:[/bold] {info.description}\n"
        f"[bold]Class:[/bold]       {type(eng).__module__}.{type(eng).__qualname__}",
        title=f"Engine: {info.name}",
        border_style="cyan",
    )
    console.print(panel)
