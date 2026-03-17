"""Custom exception hierarchy for VoiceForge."""


class VoiceForgeError(Exception):
    """Base exception for all VoiceForge errors."""


class VoiceNotFoundError(VoiceForgeError):
    """Raised when a voice directory does not exist."""


class ProfileNotFoundError(VoiceForgeError):
    """Raised when a voice profile file does not exist."""


class EngineNotFoundError(VoiceForgeError):
    """Raised when an engine name is not in the registry."""


class EngineLoadError(VoiceForgeError):
    """Raised when an engine fails to load its model."""


class InvalidAudioError(VoiceForgeError):
    """Raised when an audio file is invalid or unreadable."""


class NoClipsError(VoiceForgeError):
    """Raised when no audio clips are found for extraction."""


class ConfigError(VoiceForgeError):
    """Raised for configuration-related errors."""
