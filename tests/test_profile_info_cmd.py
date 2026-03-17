"""Tests for the profile info CLI command."""

from __future__ import annotations

from pathlib import Path

import torch
from typer.testing import CliRunner

from voiceforge.cli.app import app
from voiceforge.exceptions import ProfileNotFoundError
from voiceforge.profile.schema import VoiceProfile

runner = CliRunner()


def test_profile_info(tmp_voices_dir: Path, dummy_tensors: dict[str, torch.Tensor]) -> None:
    """profile info should display metadata and tensors."""
    voice_name = "infotest"
    profiles_dir = tmp_voices_dir / voice_name / "profiles"
    profiles_dir.mkdir(parents=True)

    profile = VoiceProfile.create(
        engine_name="indextts2",
        engine_version="2.0.0",
        source_clips_count=3,
        best_clip_name="clip_01.wav",
        best_clip_duration=5.0,
        tensors=dummy_tensors,
        label="test label",
        notes="test notes",
    )
    profile.save(profiles_dir / "indextts2.pt")

    result = runner.invoke(app, ["profile", "info", "--voice", voice_name])
    assert result.exit_code == 0
    assert "indextts2" in result.output
    assert "2.0.0" in result.output
    assert "3" in result.output  # source_clips_count
    assert "style" in result.output


def test_profile_info_not_found(tmp_voices_dir: Path) -> None:
    """profile info for missing profile should raise ProfileNotFoundError."""
    result = runner.invoke(app, ["profile", "info", "--voice", "nonexistent"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ProfileNotFoundError)
