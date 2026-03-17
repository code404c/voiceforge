"""Tests for the profile extract CLI command — using mock engine to avoid GPU."""

from __future__ import annotations

import wave
from pathlib import Path

import pytest
import torch
from typer.testing import CliRunner

from voiceforge.cli.app import app
from voiceforge.engine.base import EngineInfo, ProfileData, TTSEngine

runner = CliRunner()


class MockExtractEngine(TTSEngine):
    """A mock engine that returns dummy profile data."""

    def __init__(self, *, fail_clips: list[str] | None = None) -> None:
        self.fail_clips = fail_clips or []

    def info(self) -> EngineInfo:
        return EngineInfo(name="indextts2", version="2.0.0", description="Mock engine")

    def extract_profile(self, clips_dir, *, max_clips=None):
        tensors = {
            "style": torch.randn(1, 192),
            "spk_cond": torch.randn(1, 50, 1024),
            "s2mel_prompt": torch.randn(1, 100, 80),
            "mel": torch.randn(1, 80, 200),
        }
        metadata = {
            "source_clips_count": 3,
            "failed_clips": self.fail_clips,
            "best_clip_name": "clip_01.wav",
            "best_clip_duration": 5.0,
        }
        return ProfileData(tensors=tensors, metadata=metadata)

    def synthesize(self, profile, text, output_path, *, emotion_text=None, emotion_alpha=1.0):
        raise NotImplementedError


def _make_wav(path: Path) -> None:
    """Create a minimal valid WAV file."""
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00" * 32000)


@pytest.fixture()
def voice_with_clips(tmp_voices_dir: Path) -> str:
    """Create a voice directory with clips, return the voice name."""
    voice_name = "extracttest"
    clips_dir = tmp_voices_dir / voice_name / "clips"
    clips_dir.mkdir(parents=True)
    _make_wav(clips_dir / "clip_01.wav")
    _make_wav(clips_dir / "clip_02.wav")
    return voice_name


def test_extract_no_clips_dir(tmp_voices_dir: Path) -> None:
    """extract with a missing clips dir should raise NoClipsError."""
    from voiceforge.exceptions import NoClipsError

    result = runner.invoke(
        app,
        [
            "profile",
            "extract",
            "--voice",
            "nonexistent",
        ],
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, NoClipsError)


def test_extract_success(voice_with_clips: str, tmp_voices_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """extract with a mock engine should save a profile and exit 0."""
    monkeypatch.setattr("voiceforge.cli.profile_cmd.get_engine", lambda name: MockExtractEngine())

    result = runner.invoke(
        app,
        [
            "profile",
            "extract",
            "--voice",
            voice_with_clips,
        ],
    )

    assert result.exit_code == 0
    assert "saved" in result.output.lower() or "Profile saved" in result.output

    # Profile file should exist
    profile_path = tmp_voices_dir / voice_with_clips / "profiles" / "indextts2.pt"
    assert profile_path.exists()


def test_extract_with_failed_clips(voice_with_clips: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """extract with some failed clips should show a warning."""
    engine = MockExtractEngine(fail_clips=["bad_clip.wav"])
    monkeypatch.setattr("voiceforge.cli.profile_cmd.get_engine", lambda name: engine)

    result = runner.invoke(
        app,
        [
            "profile",
            "extract",
            "--voice",
            voice_with_clips,
        ],
    )

    assert result.exit_code == 0
    assert "bad_clip.wav" in result.output or "failed" in result.output.lower()
