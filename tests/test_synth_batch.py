"""Tests for synth batch command."""

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


class MockBatchEngine(TTSEngine):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def info(self) -> EngineInfo:
        return EngineInfo(name="mock", version="0.0.1", description="Mock")

    def extract_profile(self, clips_dir, *, max_clips=None):
        raise NotImplementedError

    def synthesize(self, profile, text, output_path, *, emotion_text=None, emotion_alpha=1.0):
        self.calls.append(text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"RIFF" + b"\x00" * 100)
        return output_path


@pytest.fixture()
def voice_with_profile(tmp_voices_dir: Path) -> str:
    name = "batchtest"
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


def test_batch_synth(voice_with_profile: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Batch synth should generate one WAV per line."""
    mock = MockBatchEngine()
    monkeypatch.setattr("voiceforge.cli.synth_cmd.get_engine", lambda name: mock)

    input_file = tmp_path / "lines.txt"
    input_file.write_text("Hello world\nGoodbye world\nThird line\n")
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        ["synth", "batch", "-v", voice_with_profile, "-i", str(input_file), "-o", str(output_dir)],
    )
    assert result.exit_code == 0
    assert len(mock.calls) == 3
    assert (output_dir / "0001.wav").exists()
    assert (output_dir / "0002.wav").exists()
    assert (output_dir / "0003.wav").exists()


def test_batch_synth_empty_file(voice_with_profile: str, tmp_path: Path) -> None:
    """Batch synth with empty file should fail."""
    input_file = tmp_path / "empty.txt"
    input_file.write_text("\n\n\n")
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        ["synth", "batch", "-v", voice_with_profile, "-i", str(input_file), "-o", str(output_dir)],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, ConfigError)


def test_batch_synth_missing_file(voice_with_profile: str, tmp_path: Path) -> None:
    """Batch synth with missing input file should fail."""
    result = runner.invoke(
        app,
        ["synth", "batch", "-v", voice_with_profile, "-i", "/nonexistent/file.txt", "-o", str(tmp_path / "out")],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, ConfigError)
