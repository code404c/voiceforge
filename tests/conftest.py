"""Shared fixtures for VoiceForge tests."""

from __future__ import annotations

import wave
from pathlib import Path

import pytest
import torch


@pytest.fixture()
def tmp_voices_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary voices directory and monkeypatch config.VOICES_DIR.

    The directory is created with the standard voice structure:
        <tmp>/voices/
    """
    voices = tmp_path / "voices"
    voices.mkdir()

    # Patch the module-level VOICES_DIR so that config helpers and CLI
    # commands that already imported it all point to the temp directory.
    import voiceforge.config as _cfg

    monkeypatch.setattr(_cfg, "VOICES_DIR", voices)

    # voice_cmd.py imports VOICES_DIR at module level — patch it there too
    # so that CLI tests see the temp directory.
    try:
        import voiceforge.cli.voice_cmd as _vcmd

        monkeypatch.setattr(_vcmd, "VOICES_DIR", voices)
    except ImportError:
        pass

    return voices


@pytest.fixture()
def dummy_tensors() -> dict[str, torch.Tensor]:
    """Return dummy tensors matching the indextts2 profile shape."""
    return {
        "style": torch.randn(1, 192),
        "spk_cond": torch.randn(1, 50, 1024),
        "s2mel_prompt": torch.randn(1, 100, 80),
        "mel": torch.randn(1, 80, 200),
    }


@pytest.fixture()
def sample_wav(tmp_path: Path) -> Path:
    """Create a minimal valid WAV file (16-bit, 16 kHz, 1 second of silence)."""
    wav_path = tmp_path / "silence.wav"
    n_channels = 1
    sample_width = 2  # 16-bit
    framerate = 16000
    n_frames = framerate  # 1 second

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(framerate)
        wf.writeframes(b"\x00" * (n_frames * sample_width * n_channels))

    return wav_path


@pytest.fixture()
def v1_profile(tmp_path: Path, dummy_tensors: dict[str, torch.Tensor]) -> Path:
    """Create a v1-format .pt file matching extract_voice_profile.py output."""
    profile_path = tmp_path / "v1_profile.pt"
    data = {
        "style": dummy_tensors["style"],
        "spk_cond": dummy_tensors["spk_cond"],
        "s2mel_prompt": dummy_tensors["s2mel_prompt"],
        "mel": dummy_tensors["mel"],
        "source_clips": 5,
        "best_clip": "best.wav",
        "version": "1.0",
    }
    torch.save(data, profile_path)
    return profile_path
