"""TTSEngine abstract base class and supporting dataclasses."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from torch import Tensor

from voiceforge.profile.schema import VoiceProfile


@dataclass
class ProfileData:
    """Container for extracted voice profile tensors + metadata."""
    tensors: dict[str, Tensor]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineInfo:
    """Static information about a TTS engine."""
    name: str
    version: str
    description: str


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    def info(self) -> EngineInfo:
        """Return static engine information (no model loading required)."""
        ...

    @abstractmethod
    def extract_profile(
        self,
        clips_dir: Path,
        *,
        max_clips: int | None = None,
    ) -> ProfileData:
        """Extract a voice profile from audio clips.

        Args:
            clips_dir: Directory containing WAV files.
            max_clips: Optional limit on number of clips to process.

        Returns:
            ProfileData with extracted tensors and metadata.
        """
        ...

    @abstractmethod
    def synthesize(
        self,
        profile: VoiceProfile,
        text: str,
        output_path: Path,
        *,
        emotion_text: str | None = None,
        emotion_alpha: float = 1.0,
    ) -> Path:
        """Synthesize speech from a voice profile.

        Args:
            profile: Loaded VoiceProfile.
            text: Text to synthesize.
            output_path: Where to write the output WAV.
            emotion_text: Optional text for emotion detection.
            emotion_alpha: Emotion blending strength (0-1).

        Returns:
            Path to the generated audio file.
        """
        ...
