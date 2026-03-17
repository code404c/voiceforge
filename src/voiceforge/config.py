"""Configuration: config file, environment variables, and default path resolution.

Priority (highest to lowest): CLI flag > env var > config file > default.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# XDG base directories
_XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
_XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))

CONFIG_DIR = _XDG_CONFIG_HOME / "voiceforge"
CONFIG_FILE = CONFIG_DIR / "config.toml"

_DEFAULT_VOICES_DIR = _XDG_DATA_HOME / "voiceforge" / "voices"

# Legacy default: <repo>/data/voices (used before XDG migration)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LEGACY_VOICES_DIR = _PROJECT_ROOT / "data" / "voices"


def _load_toml(path: Path) -> dict:
    """Load a TOML file, using tomllib (3.11+) or tomli (3.10 backport)."""
    if not path.is_file():
        return {}
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            logger.debug("tomli not available, skipping config file %s", path)
            return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


@dataclass
class VoiceForgeConfig:
    """Resolved configuration with source tracking."""

    voices_dir: Path = field(default_factory=lambda: _DEFAULT_VOICES_DIR)
    default_engine: str = "indextts2"
    indextts_root: str | None = None

    @staticmethod
    def load() -> VoiceForgeConfig:
        """Load config from file + env vars with correct priority."""
        file_data = _load_toml(CONFIG_FILE)
        cfg = VoiceForgeConfig()

        # Config file values (lowest priority)
        if "voices_dir" in file_data:
            cfg.voices_dir = Path(file_data["voices_dir"]).expanduser()
        if "default_engine" in file_data:
            cfg.default_engine = file_data["default_engine"]
        if "indextts_root" in file_data:
            cfg.indextts_root = file_data["indextts_root"]

        # Env vars override config file
        env_voices = os.environ.get("VOICEFORGE_VOICES_DIR")
        if env_voices:
            cfg.voices_dir = Path(env_voices)

        env_engine = os.environ.get("VOICEFORGE_DEFAULT_ENGINE")
        if env_engine:
            cfg.default_engine = env_engine

        env_indextts = os.environ.get("VOICEFORGE_INDEXTTS_ROOT")
        if env_indextts:
            cfg.indextts_root = env_indextts

        return cfg


def _resolve_voices_dir(cfg: VoiceForgeConfig) -> Path:
    """Pick the voices directory, preserving backward compatibility.

    Priority: env var > config file > XDG path (if exists) > legacy path (if exists) > XDG default.
    """
    # If explicitly set (env or config), use it
    env_override = os.environ.get("VOICEFORGE_VOICES_DIR")
    if env_override:
        return Path(env_override)

    file_data = _load_toml(CONFIG_FILE)
    if "voices_dir" in file_data:
        return Path(file_data["voices_dir"]).expanduser()

    # Auto-detect
    if _DEFAULT_VOICES_DIR.is_dir():
        return _DEFAULT_VOICES_DIR
    if _LEGACY_VOICES_DIR.is_dir():
        logger.info(
            "Using legacy voices dir %s (migrate to %s or set VOICEFORGE_VOICES_DIR)",
            _LEGACY_VOICES_DIR,
            _DEFAULT_VOICES_DIR,
        )
        return _LEGACY_VOICES_DIR
    return _DEFAULT_VOICES_DIR


# Module-level resolved config
_config = VoiceForgeConfig.load()
VOICES_DIR = _resolve_voices_dir(_config)
DEFAULT_ENGINE = _config.default_engine
logger.debug("VOICES_DIR resolved to %s", VOICES_DIR)


def get_config() -> VoiceForgeConfig:
    """Return the current resolved configuration."""
    return _config


def get_voice_dir(name: str) -> Path:
    """Return the directory for a voice by name."""
    return VOICES_DIR / name


def get_clips_dir(name: str) -> Path:
    return get_voice_dir(name) / "clips"


def get_profiles_dir(name: str) -> Path:
    return get_voice_dir(name) / "profiles"


def get_profile_path(name: str, engine: str) -> Path:
    """Return the profile path for a voice+engine combination."""
    return get_profiles_dir(name) / f"{engine}.pt"


def list_voice_names() -> list[str]:
    """List all voice names (directories under VOICES_DIR)."""
    if not VOICES_DIR.is_dir():
        return []
    return sorted(d.name for d in VOICES_DIR.iterdir() if d.is_dir() and not d.name.startswith("."))
