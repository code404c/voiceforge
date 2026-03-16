"""Audio file scanning and validation utilities."""

from __future__ import annotations

import struct
import wave
from pathlib import Path

SUPPORTED_EXTENSIONS = {".wav"}


def scan_clips(clips_dir: Path) -> list[Path]:
    """Return sorted list of WAV files in a directory."""
    if not clips_dir.is_dir():
        return []
    return sorted(f for f in clips_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS)


def get_duration(path: Path) -> float:
    """Get duration of a WAV file in seconds using stdlib only."""
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        if rate == 0:
            return 0.0
        return frames / rate


def validate_audio(path: Path) -> tuple[bool, str]:
    """Validate that a file is a readable WAV.

    Returns (ok, message).
    """
    if not path.exists():
        return False, f"File not found: {path}"
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported format: {path.suffix}"
    try:
        with wave.open(str(path), "rb") as wf:
            if wf.getnframes() == 0:
                return False, "Empty audio file (0 frames)"
            if wf.getframerate() == 0:
                return False, "Invalid sample rate (0)"
        return True, "ok"
    except (wave.Error, struct.error, EOFError) as e:
        return False, f"Invalid WAV file: {e}"
