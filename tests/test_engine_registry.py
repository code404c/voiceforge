"""Tests for voiceforge.engine.registry — engine registration and discovery."""

from __future__ import annotations

import pytest

from voiceforge.engine import get_engine, list_engines
from voiceforge.engine.base import EngineInfo, TTSEngine
from voiceforge.engine.registry import _registry, register


class _DummyEngine(TTSEngine):
    """Minimal concrete TTSEngine for testing."""

    def info(self) -> EngineInfo:
        return EngineInfo(
            name="dummy_test",
            version="0.0.1",
            description="Dummy engine for unit tests",
        )

    def extract_profile(self, clips_dir, *, max_clips=None):
        raise NotImplementedError

    def synthesize(self, profile, text, output_path, *, emotion_text=None, emotion_alpha=1.0):
        raise NotImplementedError


@pytest.fixture(autouse=True)
def _clean_registry():
    """Save and restore registry state around each test."""
    saved = dict(_registry)
    yield
    _registry.clear()
    _registry.update(saved)


def test_register_and_get() -> None:
    """Registering a dummy engine and retrieving it should return an instance."""

    @register("test_dummy_a")
    class DummyA(_DummyEngine):
        pass

    engine = get_engine("test_dummy_a")
    assert isinstance(engine, DummyA)
    assert isinstance(engine, TTSEngine)


def test_list_engines() -> None:
    """list_engines should include a registered dummy engine's info."""

    @register("test_dummy_b")
    class DummyB(_DummyEngine):
        def info(self) -> EngineInfo:
            return EngineInfo(
                name="test_dummy_b",
                version="0.0.1",
                description="B engine",
            )

    infos = list_engines()
    names = [info.name for info in infos]
    assert "test_dummy_b" in names


def test_unknown_engine() -> None:
    """Getting a non-existent engine should raise KeyError."""
    with pytest.raises(KeyError, match="Unknown engine"):
        get_engine("nonexistent_engine_xyz")


def test_duplicate_register() -> None:
    """Registering the same engine name twice should raise ValueError."""

    @register("test_dummy_dup")
    class DummyDup1(_DummyEngine):
        pass

    with pytest.raises(ValueError, match="already registered"):

        @register("test_dummy_dup")
        class DummyDup2(_DummyEngine):
            pass


def test_empty_registry() -> None:
    """An empty registry should return empty list and raise on get."""
    _registry.clear()

    assert list_engines() == []
    with pytest.raises(KeyError, match="Unknown engine"):
        get_engine("anything")
