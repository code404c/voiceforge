"""VoiceForge CLI — main application entry point."""

from __future__ import annotations

import typer

# Trigger engine auto-registration on import
import voiceforge.engine.indextts2  # noqa: F401
from voiceforge.cli.config_cmd import app as config_app
from voiceforge.cli.engine_cmd import app as engine_app
from voiceforge.cli.profile_cmd import app as profile_app
from voiceforge.cli.synth_cmd import app as synth_app
from voiceforge.cli.voice_cmd import app as voice_app
from voiceforge.exceptions import VoiceForgeError

app = typer.Typer(help="VoiceForge — voice cloning CLI tool.")

app.add_typer(voice_app, name="voice", help="Manage voice directories and clips.")
app.add_typer(profile_app, name="profile", help="Extract and inspect voice profiles.")
app.add_typer(synth_app, name="synth", help="Synthesize speech from a voice profile.")
app.add_typer(engine_app, name="engine", help="List and inspect TTS engines.")
app.add_typer(config_app, name="config", help="Show and manage configuration.")


def _version_callback(value: bool) -> None:
    if value:
        from voiceforge import __version__

        typer.echo(f"voiceforge {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase log verbosity (-v INFO, -vv DEBUG)."),
    version: bool = typer.Option(  # noqa: ARG001
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """VoiceForge — voice cloning CLI tool."""
    from voiceforge.logging import setup_logging

    setup_logging(verbosity=verbose)

    if ctx.invoked_subcommand is None:
        import click

        click.echo(ctx.get_help())
        raise typer.Exit()


def cli() -> None:
    """Entry point wrapper that catches VoiceForgeError for clean CLI output."""
    import sys

    from rich.console import Console

    try:
        app()
    except VoiceForgeError as exc:
        Console(stderr=True).print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
