"""Tests for voiceforge.config — path resolution and voice listing."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_voices_dir_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """VOICEFORGE_VOICES_DIR env var should override the default."""
    custom = tmp_path / "custom_voices"
    custom.mkdir()
    monkeypatch.setenv("VOICEFORGE_VOICES_DIR", str(custom))

    # Re-import to pick up the env var
    import importlib

    import voiceforge.config as cfg

    importlib.reload(cfg)

    assert custom == cfg.VOICES_DIR


def test_list_voice_names_empty(tmp_voices_dir: Path) -> None:
    """An empty voices directory should return an empty list."""
    from voiceforge.config import list_voice_names

    assert list_voice_names() == []


def test_list_voice_names(tmp_voices_dir: Path) -> None:
    """list_voice_names should return sorted directory names, ignoring dotfiles."""
    (tmp_voices_dir / "bob").mkdir()
    (tmp_voices_dir / "alice").mkdir()
    (tmp_voices_dir / ".hidden").mkdir()

    from voiceforge.config import list_voice_names

    names = list_voice_names()
    assert names == ["alice", "bob"]


def test_list_voice_names_no_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If VOICES_DIR does not exist, list_voice_names returns []."""
    import voiceforge.config as cfg

    monkeypatch.setattr(cfg, "VOICES_DIR", tmp_path / "nonexistent")

    from voiceforge.config import list_voice_names

    assert list_voice_names() == []


def test_get_voice_dir(tmp_voices_dir: Path) -> None:
    """get_voice_dir should return VOICES_DIR / name."""
    from voiceforge.config import get_voice_dir

    assert get_voice_dir("alice") == tmp_voices_dir / "alice"


def test_get_profile_path(tmp_voices_dir: Path) -> None:
    """get_profile_path should build the correct nested path."""
    from voiceforge.config import get_profile_path

    path = get_profile_path("alice", "indextts2")
    assert path == tmp_voices_dir / "alice" / "profiles" / "indextts2.pt"
