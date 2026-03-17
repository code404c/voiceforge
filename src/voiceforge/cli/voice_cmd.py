"""Voice management commands — list, inspect, export, import."""

from __future__ import annotations

import tarfile
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from voiceforge.audio.utils import get_duration, scan_clips
from voiceforge.config import VOICES_DIR, get_clips_dir, get_profiles_dir, get_voice_dir, list_voice_names
from voiceforge.engine import list_engines
from voiceforge.exceptions import ConfigError, VoiceNotFoundError

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


@app.command("export")
def voice_export(
    name: str = typer.Argument(..., help="Voice name to export"),
    output: Path = typer.Option(None, "--output", "-o", help="Output .tar.gz path (default: <name>.tar.gz)"),
) -> None:
    """Export a voice (clips + profiles) as a tar.gz archive."""
    voice_dir = get_voice_dir(name)
    if not voice_dir.is_dir():
        raise VoiceNotFoundError(f"Voice '{name}' not found at {voice_dir}")

    if output is None:
        output = Path(f"{name}.tar.gz")

    with tarfile.open(output, "w:gz") as tar:
        tar.add(voice_dir, arcname=name)

    console.print(f"[green]Exported '{name}' to {output}[/green]")


@app.command("import")
def voice_import(
    archive: Path = typer.Argument(..., help="Path to .tar.gz voice archive"),
    name: str | None = typer.Option(None, "--name", "-n", help="Override voice name (default: from archive)"),
) -> None:
    """Import a voice from a .tar.gz archive."""
    if not archive.is_file():
        raise ConfigError(f"Archive not found: {archive}")

    with tarfile.open(archive, "r:gz") as tar:
        # Determine voice name from archive top-level directory
        members = tar.getnames()
        if not members:
            raise ConfigError("Archive is empty")

        # Security: check for path traversal
        for member_name in members:
            if member_name.startswith("/") or ".." in member_name:
                raise ConfigError(f"Unsafe path in archive: {member_name}")

        archive_root = members[0].split("/")[0]
        voice_name = name or archive_root

        target_dir = get_voice_dir(voice_name)
        if target_dir.is_dir():
            raise ConfigError(f"Voice '{voice_name}' already exists at {target_dir}. Remove it first or use --name.")

        # Extract, renaming the root if needed
        for member in tar.getmembers():
            if name and member.name.startswith(archive_root):
                member.name = member.name.replace(archive_root, voice_name, 1)
            tar.extract(member, VOICES_DIR, filter="data")

    console.print(f"[green]Imported voice '{voice_name}' to {target_dir}[/green]")
