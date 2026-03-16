"""Tests for the synth CLI command — using mock engine to avoid GPU."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
from typer.testing import CliRunner

from voiceforge.cli.app import app
from voiceforge.engine.base import EngineInfo, TTSEngine
from voiceforge.profile.schema import VoiceProfile

runner = CliRunner()


class MockEngine(TTSEngine):
    """A mock TTS engine that writes a fake WAV file."""

    def info(self) -> EngineInfo:
        return EngineInfo(name="mock", version="0.0.1", description="Mock engine")

    def extract_profile(self, clips_dir, *, max_clips=None):
        raise NotImplementedError

    def synthesize(self, profile, text, output_path, *, emotion_text=None, emotion_alpha=1.0):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"RIFF" + b"\x00" * 100)
        return output_path


@pytest.fixture()
def voice_with_profile(tmp_voices_dir: Path, dummy_tensors: dict[str, torch.Tensor]) -> str:
    """Create a voice with a saved profile, return the voice name."""
    voice_name = "testvoice"
    profiles_dir = tmp_voices_dir / voice_name / "profiles"
    profiles_dir.mkdir(parents=True)

    profile = VoiceProfile.create(
        engine_name="indextts2",
        engine_version="2.0.0",
        source_clips_count=1,
        best_clip_name="clip.wav",
        best_clip_duration=2.0,
        tensors=dummy_tensors,
    )
    profile.save(profiles_dir / "indextts2.pt")
    return voice_name


def test_synth_missing_profile(tmp_voices_dir: Path) -> None:
    """synth with a missing profile should exit with code 1."""
    result = runner.invoke(
        app,
        [
            "synth",
            "--voice",
            "nonexistent",
            "--text",
            "hello",
            "--output",
            "/tmp/test_synth_out.wav",
        ],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "Profile not found" in result.output


def test_synth_success(voice_with_profile: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """synth with a valid profile and mock engine should succeed."""
    output_wav = tmp_path / "output.wav"

    # Monkeypatch get_engine to return our mock
    monkeypatch.setattr("voiceforge.cli.synth_cmd.get_engine", lambda name: MockEngine())

    result = runner.invoke(
        app,
        [
            "synth",
            "--voice",
            voice_with_profile,
            "--text",
            "Hello world",
            "--output",
            str(output_wav),
        ],
    )

    assert result.exit_code == 0
    assert "saved" in result.output.lower() or "Audio saved" in result.output
    assert output_wav.exists()


def test_synth_with_emotion(voice_with_profile: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """synth with emotion text should pass through to the engine."""
    output_wav = tmp_path / "emo_output.wav"

    mock_engine = MockEngine()
    original_synthesize = mock_engine.synthesize
    called_with: dict = {}

    def track_synthesize(profile, text, output_path, *, emotion_text=None, emotion_alpha=1.0):
        called_with["emotion_text"] = emotion_text
        called_with["emotion_alpha"] = emotion_alpha
        return original_synthesize(profile, text, output_path, emotion_text=emotion_text, emotion_alpha=emotion_alpha)

    mock_engine.synthesize = track_synthesize
    monkeypatch.setattr("voiceforge.cli.synth_cmd.get_engine", lambda name: mock_engine)

    result = runner.invoke(
        app,
        [
            "synth",
            "--voice",
            voice_with_profile,
            "--text",
            "Sad text",
            "--output",
            str(output_wav),
            "--emotion-text",
            "I am sad",
            "--emotion-alpha",
            "0.5",
        ],
    )

    assert result.exit_code == 0
    assert called_with["emotion_text"] == "I am sad"
    assert called_with["emotion_alpha"] == pytest.approx(0.5)
