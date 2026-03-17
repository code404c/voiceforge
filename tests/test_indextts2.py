"""Tests for voiceforge.engine.indextts2 — logic tests that don't require GPU."""

from __future__ import annotations

import wave
from pathlib import Path

import pytest

from voiceforge.engine.indextts2 import IndexTTS2Engine, _find_indextts_root
from voiceforge.exceptions import NoClipsError


def _make_wav(path: Path, duration_s: float = 1.0) -> None:
    """Create a minimal valid WAV file with a given duration."""
    framerate = 16000
    n_frames = int(framerate * duration_s)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(b"\x00" * (n_frames * 2))


class TestSelectBestClip:
    """Tests for IndexTTS2Engine._select_best_clip."""

    def setup_method(self) -> None:
        # Create engine without loading model
        self.engine = IndexTTS2Engine()

    def test_selects_longest_under_15s(self, tmp_path: Path) -> None:
        """Should pick the longest clip that's <= 15s."""
        short = tmp_path / "short.wav"
        medium = tmp_path / "medium.wav"
        long = tmp_path / "long.wav"
        _make_wav(short, 2.0)
        _make_wav(medium, 8.0)
        _make_wav(long, 12.0)

        best = self.engine._select_best_clip([short, medium, long])
        assert best == long

    def test_skips_over_15s(self, tmp_path: Path) -> None:
        """Clips over 15s should be skipped in favor of shorter ones."""
        short = tmp_path / "short.wav"
        too_long = tmp_path / "toolong.wav"
        _make_wav(short, 5.0)
        _make_wav(too_long, 20.0)

        best = self.engine._select_best_clip([short, too_long])
        assert best == short

    def test_all_over_15s_picks_first(self, tmp_path: Path) -> None:
        """If all clips > 15s, fall back to the first clip."""
        a = tmp_path / "a.wav"
        b = tmp_path / "b.wav"
        _make_wav(a, 20.0)
        _make_wav(b, 25.0)

        best = self.engine._select_best_clip([a, b])
        assert best == a

    def test_empty_clips_raises(self) -> None:
        """Empty clip list should raise NoClipsError."""
        with pytest.raises(NoClipsError, match="No successful clips"):
            self.engine._select_best_clip([])

    def test_single_clip(self, tmp_path: Path) -> None:
        """A single clip should be returned regardless."""
        clip = tmp_path / "only.wav"
        _make_wav(clip, 7.0)

        best = self.engine._select_best_clip([clip])
        assert best == clip


class TestFindIndexttsRoot:
    """Tests for _find_indextts_root resolution logic."""

    def test_env_var_valid(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """VOICEFORGE_INDEXTTS_ROOT should be used if set and exists."""
        monkeypatch.setenv("VOICEFORGE_INDEXTTS_ROOT", str(tmp_path))
        assert _find_indextts_root() == tmp_path

    def test_env_var_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Non-existent VOICEFORGE_INDEXTTS_ROOT should raise FileNotFoundError."""
        monkeypatch.setenv("VOICEFORGE_INDEXTTS_ROOT", "/nonexistent/path")
        with pytest.raises(FileNotFoundError, match="VOICEFORGE_INDEXTTS_ROOT"):
            _find_indextts_root()

    def test_no_env_no_package(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing env var and package should raise ImportError."""
        monkeypatch.delenv("VOICEFORGE_INDEXTTS_ROOT", raising=False)
        # Hide indextts from import
        import sys

        monkeypatch.setitem(sys.modules, "indextts", None)
        with pytest.raises(ImportError, match="indextts package not found"):
            _find_indextts_root()

    def test_engine_info(self) -> None:
        """info() should return correct engine metadata."""
        engine = IndexTTS2Engine()
        info = engine.info()
        assert info.name == "indextts2"
        assert info.version == "2.0.0"


class TestExtractProfileEdgeCases:
    """Test extract_profile error paths that don't need GPU."""

    def test_empty_clips_dir(self, tmp_path: Path) -> None:
        """extract_profile on an empty directory should raise NoClipsError."""
        engine = IndexTTS2Engine()
        engine._tts = "fake"  # bypass _ensure_loaded

        with pytest.raises(NoClipsError, match="No WAV files"):
            engine.extract_profile(tmp_path)

    def test_nonexistent_clips_dir(self, tmp_path: Path) -> None:
        """extract_profile on a non-existent directory should raise NoClipsError."""
        engine = IndexTTS2Engine()
        engine._tts = "fake"

        with pytest.raises(NoClipsError, match="No WAV files"):
            engine.extract_profile(tmp_path / "does_not_exist")
