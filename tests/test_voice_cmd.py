"""Tests for voice list, info, export, import CLI commands."""

from __future__ import annotations

import tarfile
import wave
from pathlib import Path

import pytest
import torch
from typer.testing import CliRunner

from voiceforge.cli.app import app
from voiceforge.exceptions import ConfigError, VoiceNotFoundError
from voiceforge.profile.schema import VoiceProfile

runner = CliRunner()


def _make_wav(path: Path, duration_s: float = 1.0) -> None:
    """Create a minimal valid WAV file."""
    framerate = 16000
    n_frames = int(framerate * duration_s)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(b"\x00" * (n_frames * 2))


@pytest.fixture()
def voice_with_data(tmp_voices_dir: Path) -> str:
    """Create a voice directory with clips and a profile."""
    name = "alice"
    clips_dir = tmp_voices_dir / name / "clips"
    clips_dir.mkdir(parents=True)
    _make_wav(clips_dir / "clip_01.wav", 3.0)
    _make_wav(clips_dir / "clip_02.wav", 5.0)

    profiles_dir = tmp_voices_dir / name / "profiles"
    profiles_dir.mkdir()
    profile = VoiceProfile.create(
        engine_name="indextts2",
        engine_version="2.0.0",
        source_clips_count=2,
        best_clip_name="clip_02.wav",
        best_clip_duration=5.0,
        tensors={"style": torch.randn(1, 192)},
    )
    profile.save(profiles_dir / "indextts2.pt")
    return name


def test_voice_list_empty(tmp_voices_dir: Path) -> None:
    """voice list with no voices should show a warning."""
    result = runner.invoke(app, ["voice", "list"])
    assert result.exit_code == 0
    assert "No voices found" in result.output


def test_voice_info_with_data(voice_with_data: str) -> None:
    """voice info should show clips and profiles."""
    result = runner.invoke(app, ["voice", "info", voice_with_data])
    assert result.exit_code == 0
    assert "clip_01.wav" in result.output
    assert "clip_02.wav" in result.output
    assert "indextts2" in result.output


def test_voice_info_no_clips(tmp_voices_dir: Path) -> None:
    """voice info on empty voice should show warning."""
    (tmp_voices_dir / "empty_voice" / "clips").mkdir(parents=True)
    result = runner.invoke(app, ["voice", "info", "empty_voice"])
    assert result.exit_code == 0
    assert "No clips" in result.output


def test_voice_export(voice_with_data: str, tmp_path: Path) -> None:
    """voice export should create a tar.gz archive."""
    output = tmp_path / "export.tar.gz"
    result = runner.invoke(app, ["voice", "export", voice_with_data, "--output", str(output)])
    assert result.exit_code == 0
    assert output.exists()

    with tarfile.open(output, "r:gz") as tar:
        names = tar.getnames()
        assert any("clips" in n for n in names)


def test_voice_export_not_found(tmp_voices_dir: Path) -> None:
    """voice export of non-existent voice should raise."""
    result = runner.invoke(app, ["voice", "export", "nonexistent"])
    assert result.exit_code != 0
    assert isinstance(result.exception, VoiceNotFoundError)


def test_voice_import(voice_with_data: str, tmp_voices_dir: Path, tmp_path: Path) -> None:
    """voice import should extract archive into voices directory."""
    # First export
    archive = tmp_path / "test.tar.gz"
    runner.invoke(app, ["voice", "export", voice_with_data, "--output", str(archive)])

    # Import as new name
    result = runner.invoke(app, ["voice", "import", str(archive), "--name", "imported"])
    assert result.exit_code == 0
    assert (tmp_voices_dir / "imported").is_dir()
    assert (tmp_voices_dir / "imported" / "clips").is_dir()


def test_voice_import_already_exists(voice_with_data: str, tmp_voices_dir: Path, tmp_path: Path) -> None:
    """voice import should fail if the voice already exists."""
    archive = tmp_path / "test.tar.gz"
    runner.invoke(app, ["voice", "export", voice_with_data, "--output", str(archive)])

    # Try to import with same name
    result = runner.invoke(app, ["voice", "import", str(archive), "--name", voice_with_data])
    assert result.exit_code != 0
    assert isinstance(result.exception, ConfigError)


def test_voice_import_missing_archive(tmp_voices_dir: Path) -> None:
    """voice import with non-existent archive should fail."""
    result = runner.invoke(app, ["voice", "import", "/nonexistent/archive.tar.gz"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ConfigError)
