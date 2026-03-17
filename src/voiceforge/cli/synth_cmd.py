"""Speech synthesis commands (single + batch)."""

from __future__ import annotations

import re
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from voiceforge.config import DEFAULT_ENGINE, get_profile_path
from voiceforge.engine import get_engine
from voiceforge.exceptions import ConfigError, ProfileNotFoundError
from voiceforge.profile.schema import VoiceProfile

_MAX_TEXT_LENGTH = 5000

app = typer.Typer(no_args_is_help=True)
console = Console()


def _validate_text(text: str) -> str:
    """Strip control characters and validate text length."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text).strip()
    if not text:
        raise ConfigError("Text is empty after stripping control characters.")
    if len(text) > _MAX_TEXT_LENGTH:
        raise ConfigError(f"Text too long ({len(text)} chars). Maximum: {_MAX_TEXT_LENGTH}.")
    return text


def _load_profile(voice: str, engine: str) -> VoiceProfile:
    """Load a voice profile, raising ProfileNotFoundError if missing."""
    profile_path = get_profile_path(voice, engine)
    if not profile_path.exists():
        raise ProfileNotFoundError(
            f"Profile not found: {profile_path}\n"
            f"Run 'voiceforge profile extract --voice {voice}' first."
        )
    return VoiceProfile.load(profile_path)


def _validate_emotion_alpha(alpha: float) -> None:
    if not 0.0 <= alpha <= 1.0:
        raise ConfigError(f"emotion_alpha must be between 0 and 1, got {alpha}.")


@app.callback(invoke_without_command=True)
def synth(
    ctx: typer.Context,
    voice: str = typer.Option("", "--voice", "-v", help="Voice name"),
    text: str = typer.Option("", "--text", "-t", help="Text to synthesize"),
    output: Path = typer.Option(Path("output.wav"), "--output", "-o", help="Output WAV file path"),
    engine: str = typer.Option(DEFAULT_ENGINE, "--engine", "-e", help="Engine name"),
    emotion_text: str | None = typer.Option(None, "--emotion-text", help="Text for emotion detection"),
    emotion_alpha: float = typer.Option(1.0, "--emotion-alpha", help="Emotion blending strength (0-1)"),
) -> None:
    """Synthesize speech from a voice profile."""
    if ctx.invoked_subcommand is not None:
        return

    if not voice:
        console.print("[red]Error: --voice is required.[/red]")
        raise typer.Exit(code=1)
    if not text:
        console.print("[red]Error: --text is required.[/red]")
        raise typer.Exit(code=1)

    text = _validate_text(text)
    _validate_emotion_alpha(emotion_alpha)

    profile = _load_profile(voice, engine)

    console.print("[bold]Synthesizing speech[/bold]")
    console.print(f"  Voice:  [cyan]{voice}[/cyan]")
    console.print(f"  Engine: [cyan]{engine}[/cyan]")
    console.print(f"  Text:   {text[:80]}{'...' if len(text) > 80 else ''}")
    console.print(f"  Output: {output}")
    if emotion_text:
        console.print(f"  Emotion: {emotion_text} (alpha={emotion_alpha})")
    console.print()

    with console.status("[bold green]Loading engine and synthesizing..."):
        eng = get_engine(engine)
        result_path = eng.synthesize(
            profile,
            text,
            output,
            emotion_text=emotion_text,
            emotion_alpha=emotion_alpha,
        )

    console.print(f"[green]Audio saved to {result_path}[/green]")


@app.command("batch")
def synth_batch(
    voice: str = typer.Option(..., "--voice", "-v", help="Voice name"),
    input_file: Path = typer.Option(..., "--input", "-i", help="Text file (one line per utterance)"),
    output_dir: Path = typer.Option(..., "--output", "-o", help="Output directory for WAV files"),
    engine: str = typer.Option(DEFAULT_ENGINE, "--engine", "-e", help="Engine name"),
    emotion_text: str | None = typer.Option(None, "--emotion-text", help="Text for emotion detection"),
    emotion_alpha: float = typer.Option(1.0, "--emotion-alpha", help="Emotion blending strength (0-1)"),
) -> None:
    """Batch synthesize from a text file (one utterance per line)."""
    if not input_file.is_file():
        raise ConfigError(f"Input file not found: {input_file}")

    lines = [line.strip() for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ConfigError(f"No non-empty lines in {input_file}")

    _validate_emotion_alpha(emotion_alpha)

    profile = _load_profile(voice, engine)

    console.print(f"[bold]Batch synthesis: {len(lines)} utterances[/bold]")
    console.print(f"  Voice:  [cyan]{voice}[/cyan]")
    console.print(f"  Output: {output_dir}/")
    console.print()

    output_dir.mkdir(parents=True, exist_ok=True)

    with console.status("[bold green]Loading engine..."):
        eng = get_engine(engine)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Synthesizing...", total=len(lines))

        for i, text in enumerate(lines, 1):
            text = _validate_text(text)
            out_path = output_dir / f"{i:04d}.wav"
            progress.update(task, description=f"[{i}/{len(lines)}] {text[:60]}...")

            eng.synthesize(
                profile,
                text,
                out_path,
                emotion_text=emotion_text,
                emotion_alpha=emotion_alpha,
            )
            progress.advance(task)

    console.print(f"[green]Batch complete: {len(lines)} files in {output_dir}[/green]")
