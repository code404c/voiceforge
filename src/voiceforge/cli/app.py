"""VoiceForge CLI — main application entry point."""

from __future__ import annotations

import typer

# Trigger engine auto-registration on import
import voiceforge.engine.indextts2  # noqa: F401

from voiceforge.cli.voice_cmd import app as voice_app
from voiceforge.cli.profile_cmd import app as profile_app
from voiceforge.cli.synth_cmd import app as synth_app
from voiceforge.cli.engine_cmd import app as engine_app

app = typer.Typer(no_args_is_help=True, help="VoiceForge — voice cloning CLI tool.")

app.add_typer(voice_app, name="voice", help="Manage voice directories and clips.")
app.add_typer(profile_app, name="profile", help="Extract and inspect voice profiles.")
app.add_typer(synth_app, name="synth", help="Synthesize speech from a voice profile.")
app.add_typer(engine_app, name="engine", help="List and inspect TTS engines.")


if __name__ == "__main__":
    app()
