"""Profile extraction and inspection commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from voiceforge.config import get_clips_dir, get_profile_path
from voiceforge.engine import get_engine
from voiceforge.profile.schema import VoiceProfile

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("extract")
def profile_extract(
    voice: str = typer.Option(..., "--voice", "-v", help="Voice name"),
    engine: str = typer.Option("indextts2", "--engine", "-e", help="Engine name"),
) -> None:
    """Extract a voice profile from audio clips."""
    clips_dir = get_clips_dir(voice)
    if not clips_dir.is_dir():
        console.print(f"[red]Clips directory not found: {clips_dir}[/red]")
        raise typer.Exit(code=1)

    profile_path = get_profile_path(voice, engine)

    console.print("[bold]Extracting profile[/bold]")
    console.print(f"  Voice:  [cyan]{voice}[/cyan]")
    console.print(f"  Engine: [cyan]{engine}[/cyan]")
    console.print(f"  Clips:  {clips_dir}")
    console.print(f"  Output: {profile_path}")
    console.print()

    with console.status("[bold green]Loading engine and extracting profile..."):
        eng = get_engine(engine)
        profile_data = eng.extract_profile(clips_dir)

    info = eng.info()

    vp = VoiceProfile.create(
        engine_name=info.name,
        engine_version=info.version,
        source_clips_count=profile_data.metadata.get("source_clips_count", 0),
        best_clip_name=profile_data.metadata.get("best_clip_name", ""),
        best_clip_duration=profile_data.metadata.get("best_clip_duration", 0.0),
        tensors=profile_data.tensors,
    )
    vp.save(profile_path)

    failed = profile_data.metadata.get("failed_clips", [])
    if failed:
        console.print(f"[yellow]Warning: {len(failed)} clip(s) failed: {', '.join(failed)}[/yellow]")

    console.print(f"[green]Profile saved to {profile_path}[/green]")


@app.command("info")
def profile_info(
    voice: str = typer.Option(..., "--voice", "-v", help="Voice name"),
    engine: str = typer.Option("indextts2", "--engine", "-e", help="Engine name"),
) -> None:
    """Display metadata for an extracted voice profile."""
    profile_path = get_profile_path(voice, engine)
    if not profile_path.exists():
        console.print(f"[red]Profile not found: {profile_path}[/red]")
        raise typer.Exit(code=1)

    vp = VoiceProfile.load(profile_path)

    table = Table(title=f"Profile — {voice} ({engine})")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")

    table.add_row("Profile version", str(vp.profile_version))
    table.add_row("Engine", f"{vp.engine_name} {vp.engine_version}")
    table.add_row("Created at", vp.created_at or "[dim]n/a[/dim]")
    table.add_row("Source clips", str(vp.source_clips_count))
    table.add_row("Best clip", vp.best_clip_name or "[dim]n/a[/dim]")
    table.add_row("Best clip duration", f"{vp.best_clip_duration:.2f}s" if vp.best_clip_duration else "[dim]n/a[/dim]")
    table.add_row("Label", vp.label or "[dim]—[/dim]")
    table.add_row("Notes", vp.notes or "[dim]—[/dim]")

    # Tensor summary
    tensor_lines = []
    for key, tensor in sorted(vp.tensors.items()):
        tensor_lines.append(f"{key}: {list(tensor.shape)} ({tensor.dtype})")
    table.add_row("Tensors", "\n".join(tensor_lines) if tensor_lines else "[dim]none[/dim]")

    console.print(table)
    console.print(f"\n[dim]Path: {profile_path}[/dim]")
