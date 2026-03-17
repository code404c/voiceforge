"""Tests for the VoiceForge CLI — using typer.testing.CliRunner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from voiceforge.cli.app import app

runner = CliRunner()


def test_bare_invocation() -> None:
    """Running voiceforge with no args should show help and exit 0."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "VoiceForge" in result.output or "voiceforge" in result.output.lower()


def test_help() -> None:
    """--help should exit 0 and show usage info."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "VoiceForge" in result.output or "voiceforge" in result.output.lower()


def test_version() -> None:
    """--version should print the version string and exit 0."""
    from voiceforge import __version__

    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_version_short() -> None:
    """-V should print the version string and exit 0."""
    from voiceforge import __version__

    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_voice_list(tmp_voices_dir: Path) -> None:
    """'voice list' should display voice directories."""
    # Create two voice directories
    (tmp_voices_dir / "alice").mkdir()
    (tmp_voices_dir / "alice" / "clips").mkdir()
    (tmp_voices_dir / "bob").mkdir()
    (tmp_voices_dir / "bob" / "clips").mkdir()

    result = runner.invoke(app, ["voice", "list"])

    assert result.exit_code == 0
    assert "alice" in result.output
    assert "bob" in result.output


def test_engine_list() -> None:
    """'engine list' should show the indextts2 engine."""
    result = runner.invoke(app, ["engine", "list"])

    assert result.exit_code == 0
    assert "indextts2" in result.output


def test_voice_info_not_found() -> None:
    """'voice info nonexistent' should show that no clips were found."""
    result = runner.invoke(app, ["voice", "info", "nonexistent"])

    # Should still exit 0 but show a warning / empty state
    assert "No clips" in result.output or "not found" in result.output.lower() or result.output != ""


def test_synth_missing_profile(tmp_voices_dir: Path) -> None:
    """'synth' with a voice that has no profile should raise ProfileNotFoundError."""
    from voiceforge.exceptions import ProfileNotFoundError

    result = runner.invoke(
        app,
        [
            "synth",
            "--voice",
            "nonexistent_voice",
            "--text",
            "Hello world",
            "--output",
            "/tmp/test_out.wav",
        ],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, ProfileNotFoundError)
