"""Tests for voiceforge.profile.schema — VoiceProfile save/load/roundtrip."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from voiceforge.profile.schema import VoiceProfile, _MAGIC_KEY, _TENSOR_PREFIX


def test_save_load_roundtrip(tmp_path: Path, dummy_tensors: dict[str, torch.Tensor]) -> None:
    """Create -> save -> load should preserve all fields."""
    profile = VoiceProfile.create(
        engine_name="indextts2",
        engine_version="2.0.0",
        source_clips_count=3,
        best_clip_name="clip_01.wav",
        best_clip_duration=4.5,
        tensors=dummy_tensors,
        label="test label",
        notes="some notes",
    )

    save_path = tmp_path / "roundtrip.pt"
    profile.save(save_path)

    loaded = VoiceProfile.load(save_path)

    assert loaded.profile_version == profile.profile_version
    assert loaded.engine_name == profile.engine_name
    assert loaded.engine_version == profile.engine_version
    assert loaded.created_at == profile.created_at
    assert loaded.source_clips_count == profile.source_clips_count
    assert loaded.best_clip_name == profile.best_clip_name
    assert loaded.best_clip_duration == pytest.approx(profile.best_clip_duration)
    assert loaded.label == profile.label
    assert loaded.notes == profile.notes

    assert set(loaded.tensors.keys()) == set(dummy_tensors.keys())
    for key in dummy_tensors:
        assert torch.equal(loaded.tensors[key], dummy_tensors[key])


def test_v1_compatibility(v1_profile: Path) -> None:
    """A v1-format .pt file should load with engine_name='indextts2'."""
    loaded = VoiceProfile.load(v1_profile)

    assert loaded.profile_version == 1
    assert loaded.engine_name == "indextts2"
    assert loaded.engine_version == "1.0"
    assert loaded.source_clips_count == 5
    assert loaded.best_clip_name == "best.wav"
    assert "style" in loaded.tensors
    assert "spk_cond" in loaded.tensors
    assert "s2mel_prompt" in loaded.tensors
    assert "mel" in loaded.tensors


def test_magic_marker(tmp_path: Path, dummy_tensors: dict[str, torch.Tensor]) -> None:
    """Saved profile should contain the magic marker key."""
    profile = VoiceProfile.create(
        engine_name="indextts2",
        engine_version="2.0.0",
        source_clips_count=1,
        best_clip_name="clip.wav",
        best_clip_duration=1.0,
        tensors=dummy_tensors,
    )
    save_path = tmp_path / "magic.pt"
    profile.save(save_path)

    raw = torch.load(save_path, map_location="cpu", weights_only=True)
    assert _MAGIC_KEY in raw
    assert raw[_MAGIC_KEY] is True


def test_tensor_prefix(tmp_path: Path, dummy_tensors: dict[str, torch.Tensor]) -> None:
    """Tensor keys in the saved file should use the 't:' prefix."""
    profile = VoiceProfile.create(
        engine_name="indextts2",
        engine_version="2.0.0",
        source_clips_count=1,
        best_clip_name="clip.wav",
        best_clip_duration=1.0,
        tensors=dummy_tensors,
    )
    save_path = tmp_path / "prefix.pt"
    profile.save(save_path)

    raw = torch.load(save_path, map_location="cpu", weights_only=True)

    prefixed_keys = [k for k in raw if k.startswith(_TENSOR_PREFIX)]
    assert len(prefixed_keys) == len(dummy_tensors)

    for key in dummy_tensors:
        assert f"{_TENSOR_PREFIX}{key}" in raw


def test_load_nonexistent(tmp_path: Path) -> None:
    """Loading a non-existent file should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        VoiceProfile.load(tmp_path / "does_not_exist.pt")


def test_load_invalid_format(tmp_path: Path) -> None:
    """Loading a dict without magic key or v1 keys should raise ValueError."""
    bad_path = tmp_path / "bad.pt"
    torch.save({"random_key": 42, "another": "value"}, bad_path)

    with pytest.raises(ValueError, match="Unrecognized profile format"):
        VoiceProfile.load(bad_path)
