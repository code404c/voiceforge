"""Tests for engine list and engine info CLI commands."""

from __future__ import annotations

from typer.testing import CliRunner

from voiceforge.cli.app import app
from voiceforge.exceptions import EngineNotFoundError

runner = CliRunner()


def test_engine_list() -> None:
    """engine list should show registered engines."""
    result = runner.invoke(app, ["engine", "list"])
    assert result.exit_code == 0
    assert "indextts2" in result.output
    assert "2.0.0" in result.output


def test_engine_info() -> None:
    """engine info should show details for a known engine."""
    result = runner.invoke(app, ["engine", "info", "indextts2"])
    assert result.exit_code == 0
    assert "indextts2" in result.output
    assert "2.0.0" in result.output


def test_engine_info_unknown() -> None:
    """engine info for unknown engine should raise EngineNotFoundError."""
    result = runner.invoke(app, ["engine", "info", "nonexistent"])
    assert result.exit_code != 0
    assert isinstance(result.exception, EngineNotFoundError)
