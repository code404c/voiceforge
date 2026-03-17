"""Tests for voiceforge.config — path resolution, config file, and voice listing."""

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


def test_load_toml_missing(tmp_path: Path) -> None:
    """_load_toml should return {} for non-existent file."""
    from voiceforge.config import _load_toml

    assert _load_toml(tmp_path / "nope.toml") == {}


def test_load_toml_valid(tmp_path: Path) -> None:
    """_load_toml should parse a valid TOML file."""
    from voiceforge.config import _load_toml

    toml_file = tmp_path / "test.toml"
    toml_file.write_text('voices_dir = "/custom/path"\ndefault_engine = "test"\n')
    data = _load_toml(toml_file)
    assert data["voices_dir"] == "/custom/path"
    assert data["default_engine"] == "test"


def test_voiceforge_config_load_defaults() -> None:
    """VoiceForgeConfig.load with no file or env should use defaults."""
    from voiceforge.config import VoiceForgeConfig

    cfg = VoiceForgeConfig()
    assert cfg.default_engine == "indextts2"
    assert cfg.indextts_root is None


def test_voiceforge_config_load_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """VoiceForgeConfig.load should pick up env vars."""
    from voiceforge.config import VoiceForgeConfig

    monkeypatch.setenv("VOICEFORGE_DEFAULT_ENGINE", "myengine")
    monkeypatch.setenv("VOICEFORGE_INDEXTTS_ROOT", "/my/root")
    # Prevent config file from interfering
    monkeypatch.setattr("voiceforge.config.CONFIG_FILE", Path("/nonexistent/config.toml"))

    cfg = VoiceForgeConfig.load()
    assert cfg.default_engine == "myengine"
    assert cfg.indextts_root == "/my/root"


def test_voiceforge_config_load_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """VoiceForgeConfig.load should read from config file."""
    from voiceforge.config import VoiceForgeConfig

    config_file = tmp_path / "config.toml"
    config_file.write_text('voices_dir = "~/my_voices"\ndefault_engine = "fileengine"\n')

    monkeypatch.setattr("voiceforge.config.CONFIG_FILE", config_file)
    # Clear env vars
    monkeypatch.delenv("VOICEFORGE_VOICES_DIR", raising=False)
    monkeypatch.delenv("VOICEFORGE_DEFAULT_ENGINE", raising=False)
    monkeypatch.delenv("VOICEFORGE_INDEXTTS_ROOT", raising=False)

    cfg = VoiceForgeConfig.load()
    assert cfg.default_engine == "fileengine"
    assert "my_voices" in str(cfg.voices_dir)


def test_get_config() -> None:
    """get_config should return a VoiceForgeConfig instance."""
    from voiceforge.config import VoiceForgeConfig, get_config

    cfg = get_config()
    assert isinstance(cfg, VoiceForgeConfig)
