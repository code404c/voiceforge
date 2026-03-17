"""Engine registration and discovery."""

from __future__ import annotations

import logging
from collections.abc import Callable

from voiceforge.engine.base import EngineInfo, TTSEngine
from voiceforge.exceptions import EngineNotFoundError

logger = logging.getLogger(__name__)

# Registry: engine_name -> factory callable (lazy instantiation)
_registry: dict[str, Callable[[], TTSEngine]] = {}
# Cache: engine_name -> singleton instance (avoids reloading models)
_instance_cache: dict[str, TTSEngine] = {}


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
        logger.debug("Registered engine '%s' -> %s", name, cls.__name__)
        return cls

    return decorator


def get_engine(name: str) -> TTSEngine:
    """Return a cached engine instance, creating it on first call."""
    if name not in _registry:
        available = ", ".join(sorted(_registry)) or "(none)"
        raise EngineNotFoundError(f"Unknown engine '{name}'. Available: {available}")
    if name not in _instance_cache:
        logger.debug("Instantiating engine '%s'", name)
        _instance_cache[name] = _registry[name]()
    return _instance_cache[name]


def list_engines() -> list[EngineInfo]:
    """Return info for all registered engines (no model loading)."""
    infos = []
    for _name, factory in sorted(_registry.items()):
        # EngineInfo is cheap — engines should return it without loading models
        engine = factory()
        infos.append(engine.info())
    return infos
