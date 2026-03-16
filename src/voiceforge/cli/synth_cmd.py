"""Speech synthesis command."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from voiceforge.config import get_profile_path
from voiceforge.engine import get_engine
from voiceforge.profile.schema import VoiceProfile

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback(invoke_without_command=True)
def synth(
    voice: str = typer.Option(..., "--voice", "-v", help="Voice name"),
    text: str = typer.Option(..., "--text", "-t", help="Text to synthesize"),
    output: Path = typer.Option(..., "--output", "-o", help="Output WAV file path"),
    engine: str = typer.Option("indextts2", "--engine", "-e", help="Engine name"),
    emotion_text: str | None = typer.Option(None, "--emotion-text", help="Text for emotion detection"),
    emotion_alpha: float = typer.Option(1.0, "--emotion-alpha", help="Emotion blending strength (0-1)"),
) -> None:
    """Synthesize speech from a voice profile."""
    profile_path = get_profile_path(voice, engine)
    if not profile_path.exists():
        console.print(f"[red]Profile not found: {profile_path}[/red]")
        console.print(f"[dim]Run 'voiceforge profile extract --voice {voice}' first.[/dim]")
        raise typer.Exit(code=1)

    console.print(f"[bold]Synthesizing speech[/bold]")
    console.print(f"  Voice:  [cyan]{voice}[/cyan]")
    console.print(f"  Engine: [cyan]{engine}[/cyan]")
    console.print(f"  Text:   {text[:80]}{'...' if len(text) > 80 else ''}")
    console.print(f"  Output: {output}")
    if emotion_text:
        console.print(f"  Emotion: {emotion_text} (alpha={emotion_alpha})")
    console.print()

    with console.status("[bold green]Loading profile and synthesizing..."):
        profile = VoiceProfile.load(profile_path)
        eng = get_engine(engine)
        result_path = eng.synthesize(
            profile,
            text,
            output,
            emotion_text=emotion_text,
            emotion_alpha=emotion_alpha,
        )

    console.print(f"[green]Audio saved to {result_path}[/green]")
