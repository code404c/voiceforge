"""Tests for synth command input validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
from typer.testing import CliRunner

from voiceforge.cli.app import app
from voiceforge.engine.base import EngineInfo, TTSEngine
from voiceforge.exceptions import ConfigError
from voiceforge.profile.schema import VoiceProfile

runner = CliRunner()


class MockEngine(TTSEngine):
    def info(self) -> EngineInfo:
        return EngineInfo(name="mock", version="0.0.1", description="Mock")

    def extract_profile(self, clips_dir, *, max_clips=None):
        raise NotImplementedError

    def synthesize(self, profile, text, output_path, *, emotion_text=None, emotion_alpha=1.0):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"RIFF" + b"\x00" * 100)
        return output_path


@pytest.fixture()
def voice_with_profile(tmp_voices_dir: Path) -> str:
    name = "valtest"
    profiles_dir = tmp_voices_dir / name / "profiles"
    profiles_dir.mkdir(parents=True)
    profile = VoiceProfile.create(
        engine_name="indextts2",
        engine_version="2.0.0",
        source_clips_count=1,
        best_clip_name="clip.wav",
        best_clip_duration=2.0,
        tensors={"style": torch.randn(1, 192)},
    )
    profile.save(profiles_dir / "indextts2.pt")
    return name


def test_synth_empty_text(voice_with_profile: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty text should fail."""
    monkeypatch.setattr("voiceforge.cli.synth_cmd.get_engine", lambda name: MockEngine())
    result = runner.invoke(app, ["synth", "-v", voice_with_profile, "-t", "   ", "-o", "/tmp/x.wav"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ConfigError)


def test_synth_text_too_long(voice_with_profile: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Text exceeding max length should fail."""
    monkeypatch.setattr("voiceforge.cli.synth_cmd.get_engine", lambda name: MockEngine())
    long_text = "a" * 6000
    result = runner.invoke(app, ["synth", "-v", voice_with_profile, "-t", long_text, "-o", "/tmp/x.wav"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ConfigError)


def test_synth_invalid_emotion_alpha(voice_with_profile: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """emotion_alpha outside [0,1] should fail."""
    monkeypatch.setattr("voiceforge.cli.synth_cmd.get_engine", lambda name: MockEngine())
    result = runner.invoke(
        app,
        ["synth", "-v", voice_with_profile, "-t", "test", "-o", "/tmp/x.wav", "--emotion-alpha", "1.5"],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, ConfigError)


def test_synth_strips_control_chars(voice_with_profile: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Control characters should be stripped from text."""
    monkeypatch.setattr("voiceforge.cli.synth_cmd.get_engine", lambda name: MockEngine())
    out = tmp_path / "out.wav"
    result = runner.invoke(
        app, ["synth", "-v", voice_with_profile, "-t", "hello\x00world", "-o", str(out)]
    )
    assert result.exit_code == 0
