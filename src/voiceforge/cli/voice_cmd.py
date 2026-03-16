"""Voice management commands — list and inspect voice directories."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from voiceforge.audio.utils import get_duration, scan_clips
from voiceforge.config import VOICES_DIR, get_clips_dir, get_profiles_dir, list_voice_names
from voiceforge.engine import list_engines

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("list")
def voice_list() -> None:
    """List all voices in VOICES_DIR."""
    names = list_voice_names()
    if not names:
        console.print(f"[yellow]No voices found in {VOICES_DIR}[/yellow]")
        raise typer.Exit()

    engine_names = [e.name for e in list_engines()]

    table = Table(title=f"Voices — {VOICES_DIR}")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Clips", justify="right")
    for eng in engine_names:
        table.add_column(f"Profile ({eng})", justify="center")

    for name in names:
        clips = scan_clips(get_clips_dir(name))
        profiles_dir = get_profiles_dir(name)

        profile_statuses: list[str] = []
        for eng in engine_names:
            profile_path = profiles_dir / f"{eng}.pt"
            if profile_path.exists():
                profile_statuses.append("[green]yes[/green]")
            else:
                profile_statuses.append("[dim]—[/dim]")

        table.add_row(name, str(len(clips)), *profile_statuses)

    console.print(table)


@app.command("info")
def voice_info(name: str = typer.Argument(..., help="Voice name")) -> None:
    """Show detailed info about a voice."""
    clips_dir = get_clips_dir(name)
    profiles_dir = get_profiles_dir(name)

    clips = scan_clips(clips_dir)

    # Clips table
    if clips:
        clip_table = Table(title=f"Clips — {name}")
        clip_table.add_column("#", justify="right", style="dim")
        clip_table.add_column("File", style="cyan")
        clip_table.add_column("Duration", justify="right")

        total_duration = 0.0
        for i, clip in enumerate(clips, 1):
            dur = get_duration(clip)
            total_duration += dur
            clip_table.add_row(str(i), clip.name, f"{dur:.2f}s")

        clip_table.add_section()
        clip_table.add_row("", "[bold]Total[/bold]", f"[bold]{total_duration:.2f}s[/bold]")
        console.print(clip_table)
    else:
        console.print(f"[yellow]No clips found in {clips_dir}[/yellow]")

    # Profiles
    engine_infos = list_engines()
    if engine_infos:
        console.print()
        profile_table = Table(title=f"Profiles — {name}")
        profile_table.add_column("Engine", style="cyan")
        profile_table.add_column("Status", justify="center")
        profile_table.add_column("Path")

        for eng in engine_infos:
            profile_path = profiles_dir / f"{eng.name}.pt"
            status = "[green]available[/green]" if profile_path.exists() else "[dim]not extracted[/dim]"
            profile_table.add_row(eng.name, status, str(profile_path))

        console.print(profile_table)
