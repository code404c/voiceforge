"""VoiceProfile dataclass with save/load and v1 backward compatibility."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from torch import Tensor

logger = logging.getLogger(__name__)

# Magic marker to distinguish VoiceForge profiles from raw .pt files
_MAGIC_KEY = "_voiceforge_profile"
_CURRENT_VERSION = 2

# Tensor keys use "t:" prefix in the .pt file to separate from metadata
_TENSOR_PREFIX = "t:"

# Known tensor keys in a v1 profile (from extract_voice_profile.py)
_V1_TENSOR_KEYS = {"style", "spk_cond", "s2mel_prompt", "mel"}


@dataclass
class VoiceProfile:
    """Serializable voice profile with engine metadata."""

    profile_version: int
    engine_name: str
    engine_version: str
    created_at: str
    source_clips_count: int
    best_clip_name: str
    best_clip_duration: float
    tensors: dict[str, Tensor]
    label: str = ""
    notes: str = ""

    @staticmethod
    def create(
        *,
        engine_name: str,
        engine_version: str,
        source_clips_count: int,
        best_clip_name: str,
        best_clip_duration: float,
        tensors: dict[str, Tensor],
        label: str = "",
        notes: str = "",
    ) -> VoiceProfile:
        """Create a new VoiceProfile with current timestamp."""
        return VoiceProfile(
            profile_version=_CURRENT_VERSION,
            engine_name=engine_name,
            engine_version=engine_version,
            created_at=datetime.now(timezone.utc).isoformat(),
            source_clips_count=source_clips_count,
            best_clip_name=best_clip_name,
            best_clip_duration=best_clip_duration,
            tensors=tensors,
            label=label,
            notes=notes,
        )

    def save(self, path: Path) -> None:
        """Save profile to a .pt file."""
        data: dict[str, Any] = {
            _MAGIC_KEY: True,
            "profile_version": self.profile_version,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "source_clips_count": self.source_clips_count,
            "best_clip_name": self.best_clip_name,
            "best_clip_duration": self.best_clip_duration,
            "label": self.label,
            "notes": self.notes,
        }
        # Store tensors with prefix to avoid key collisions
        for key, tensor in self.tensors.items():
            data[f"{_TENSOR_PREFIX}{key}"] = tensor.cpu()

        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(data, path)
        logger.info("Profile saved to %s", path)

    @staticmethod
    def load(path: Path) -> VoiceProfile:
        """Load a profile from a .pt file, with v1 backward compatibility."""
        if not path.exists():
            raise FileNotFoundError(f"Profile not found: {path}")

        data = torch.load(path, map_location="cpu", weights_only=True)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid profile file: expected dict, got {type(data).__name__}")

        if data.get(_MAGIC_KEY):
            logger.info("Loading v2 profile from %s", path)
            return _load_v2(data)

        # Try v1 format (from extract_voice_profile.py)
        if _V1_TENSOR_KEYS.issubset(data.keys()):
            logger.info("Loading v1 profile from %s (auto-migrating)", path)
            return _load_v1(data, path)

        raise ValueError(f"Unrecognized profile format. Keys: {sorted(data.keys())}")


def _load_v2(data: dict[str, Any]) -> VoiceProfile:
    """Load a v2 (VoiceForge native) profile."""
    tensors = {}
    for key, value in data.items():
        if key.startswith(_TENSOR_PREFIX):
            tensors[key[len(_TENSOR_PREFIX) :]] = value

    return VoiceProfile(
        profile_version=data["profile_version"],
        engine_name=data["engine_name"],
        engine_version=data["engine_version"],
        created_at=data["created_at"],
        source_clips_count=data["source_clips_count"],
        best_clip_name=data["best_clip_name"],
        best_clip_duration=data.get("best_clip_duration", 0.0),
        tensors=tensors,
        label=data.get("label", ""),
        notes=data.get("notes", ""),
    )


def _load_v1(data: dict[str, Any], path: Path) -> VoiceProfile:
    """Load a v1 profile (from extract_voice_profile.py)."""
    tensors = {k: v for k, v in data.items() if isinstance(v, Tensor)}

    return VoiceProfile(
        profile_version=1,
        engine_name="indextts2",
        engine_version=data.get("version", "1.0"),
        created_at="",  # v1 didn't store timestamps
        source_clips_count=data.get("source_clips", 0),
        best_clip_name=data.get("best_clip", ""),
        best_clip_duration=0.0,  # v1 didn't store duration
        tensors=tensors,
        label="",
        notes=f"Migrated from v1: {path.name}",
    )
