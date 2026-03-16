"""Tests for voiceforge.audio.utils — audio scanning and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from voiceforge.audio.utils import get_duration, scan_clips, validate_audio


def test_scan_clips(tmp_path: Path) -> None:
    """scan_clips should return only .wav files, sorted by name."""
    (tmp_path / "b.wav").write_bytes(b"fake")
    (tmp_path / "a.wav").write_bytes(b"fake")
    (tmp_path / "notes.txt").write_text("not audio")
    (tmp_path / "data.json").write_text("{}")

    result = scan_clips(tmp_path)

    assert len(result) == 2
    assert result[0].name == "a.wav"
    assert result[1].name == "b.wav"


def test_scan_empty_dir(tmp_path: Path) -> None:
    """Empty directory should return an empty list."""
    assert scan_clips(tmp_path) == []


def test_scan_nonexistent_dir(tmp_path: Path) -> None:
    """Non-existent directory should return an empty list."""
    assert scan_clips(tmp_path / "does_not_exist") == []


def test_get_duration(sample_wav: Path) -> None:
    """Duration of the 1-second sample WAV should be approximately 1.0s."""
    duration = get_duration(sample_wav)
    assert duration == pytest.approx(1.0, abs=0.01)


def test_validate_audio_valid(sample_wav: Path) -> None:
    """A valid WAV file should pass validation."""
    ok, msg = validate_audio(sample_wav)
    assert ok is True
    assert msg == "ok"


def test_validate_audio_missing(tmp_path: Path) -> None:
    """A missing file should fail validation."""
    ok, msg = validate_audio(tmp_path / "missing.wav")
    assert ok is False
    assert "not found" in msg.lower() or "File not found" in msg


def test_validate_audio_not_wav(tmp_path: Path) -> None:
    """A non-WAV file should fail validation."""
    txt_file = tmp_path / "readme.txt"
    txt_file.write_text("hello")

    ok, msg = validate_audio(txt_file)
    assert ok is False
    assert "unsupported" in msg.lower() or "Unsupported" in msg
