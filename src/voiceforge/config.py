"""Environment variables and default path resolution."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Default: ~/.local/share/voiceforge/voices (XDG_DATA_HOME convention)
_XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
_DEFAULT_VOICES_DIR = _XDG_DATA_HOME / "voiceforge" / "voices"

VOICES_DIR = Path(os.environ.get("VOICEFORGE_VOICES_DIR", str(_DEFAULT_VOICES_DIR)))
logger.debug("VOICES_DIR resolved to %s", VOICES_DIR)


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
