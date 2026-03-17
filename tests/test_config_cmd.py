"""Tests for config show and config init CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from voiceforge.cli.app import app

runner = CliRunner()


def test_config_show() -> None:
    """config show should display configuration table."""
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "voices_dir" in result.output
    assert "default_engine" in result.output
    assert "indextts_root" in result.output


def test_config_init_creates_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config init should create a default config file."""
    import voiceforge.cli.config_cmd as cmd
    import voiceforge.config as cfg

    config_dir = tmp_path / "voiceforge"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr(cmd, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cmd, "CONFIG_FILE", config_file)
    monkeypatch.setattr(cfg, "CONFIG_FILE", config_file)

    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    assert config_file.exists()
    assert "voices_dir" in config_file.read_text()


def test_config_init_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config init should warn if config file already exists."""
    import voiceforge.cli.config_cmd as cmd

    config_dir = tmp_path / "voiceforge"
    config_dir.mkdir()
    config_file = config_dir / "config.toml"
    config_file.write_text("existing = true\n")
    monkeypatch.setattr(cmd, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cmd, "CONFIG_FILE", config_file)

    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    assert "already exists" in result.output
