"""Audio file scanning, validation, and format conversion utilities."""

from __future__ import annotations

import logging
import shutil
import struct
import subprocess
import wave
from pathlib import Path

import librosa

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".wav"}
CONVERTIBLE_EXTENSIONS = {".mp3", ".flac", ".ogg", ".m4a", ".opus"}
ALL_AUDIO_EXTENSIONS = SUPPORTED_EXTENSIONS | CONVERTIBLE_EXTENSIONS

_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def scan_clips(clips_dir: Path) -> list[Path]:
    """Return sorted list of WAV files in a directory."""
    if not clips_dir.is_dir():
        return []
    clips = sorted(f for f in clips_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS)
    logger.debug("scan_clips: found %d clip(s) in %s", len(clips), clips_dir)
    return clips


def scan_all_audio(clips_dir: Path) -> list[Path]:
    """Return sorted list of all audio files (WAV + convertible formats)."""
    if not clips_dir.is_dir():
        return []
    clips = sorted(f for f in clips_dir.iterdir() if f.suffix.lower() in ALL_AUDIO_EXTENSIONS)
    logger.debug("scan_all_audio: found %d file(s) in %s", len(clips), clips_dir)
    return clips


def get_duration(path: Path) -> float:
    """Get duration of a WAV file in seconds."""
    return librosa.get_duration(path=str(path))


def validate_audio(path: Path) -> tuple[bool, str]:
    """Validate that a file is a readable WAV.

    Returns (ok, message).
    """
    if not path.exists():
        return False, f"File not found: {path}"
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported format: {path.suffix}"
    if path.stat().st_size > _MAX_FILE_SIZE:
        return False, f"File too large: {path.stat().st_size / 1024 / 1024:.1f} MB (max {_MAX_FILE_SIZE // 1024 // 1024} MB)"
    try:
        with wave.open(str(path), "rb") as wf:
            if wf.getnframes() == 0:
                return False, "Empty audio file (0 frames)"
            if wf.getframerate() == 0:
                return False, "Invalid sample rate (0)"
        return True, "ok"
    except (wave.Error, struct.error, EOFError) as e:
        return False, f"Invalid WAV file: {e}"


def convert_to_wav(source: Path, target: Path | None = None) -> Path:
    """Convert an audio file to WAV format using ffmpeg.

    Args:
        source: Path to input audio file (.mp3, .flac, .ogg, etc.)
        target: Optional output path. Defaults to same directory with .wav extension.

    Returns:
        Path to the converted WAV file.

    Raises:
        FileNotFoundError: If source doesn't exist or ffmpeg not found.
        RuntimeError: If conversion fails.
    """
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    if target is None:
        target = source.with_suffix(".wav")

    if source.suffix.lower() == ".wav":
        if source != target:
            shutil.copy2(source, target)
        return target

    if not shutil.which("ffmpeg"):
        raise FileNotFoundError(
            "ffmpeg not found. Install it to convert non-WAV audio files.\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  macOS: brew install ffmpeg"
        )

    result = subprocess.run(
        ["ffmpeg", "-i", str(source), "-ar", "16000", "-ac", "1", "-y", str(target)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr[:500]}")

    logger.info("Converted %s -> %s", source.name, target.name)
    return target
