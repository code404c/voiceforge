"""Engine registration and discovery."""

from __future__ import annotations

from typing import Callable

from voiceforge.engine.base import EngineInfo, TTSEngine

# Registry: engine_name -> factory callable (lazy instantiation)
_registry: dict[str, Callable[[], TTSEngine]] = {}


def register(name: str) -> Callable:
    """Decorator to register a TTS engine factory.

    Usage:
        @register("indextts2")
        class IndexTTS2Engine(TTSEngine): ...
    """
    def decorator(cls: type[TTSEngine]) -> type[TTSEngine]:
        if name in _registry:
            raise ValueError(f"Engine '{name}' is already registered")
        _registry[name] = cls
        return cls
    return decorator


def get_engine(name: str) -> TTSEngine:
    """Instantiate and return an engine by name."""
    if name not in _registry:
        available = ", ".join(sorted(_registry)) or "(none)"
        raise KeyError(f"Unknown engine '{name}'. Available: {available}")
    return _registry[name]()


def list_engines() -> list[EngineInfo]:
    """Return info for all registered engines (no model loading)."""
    infos = []
    for name, factory in sorted(_registry.items()):
        # EngineInfo is cheap — engines should return it without loading models
        engine = factory()
        infos.append(engine.info())
    return infos
