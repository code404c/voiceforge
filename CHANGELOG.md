# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- README with installation guide, quick start, and CLI reference
- LICENSE (MIT)
- `--version` / `-V` flag
- CHANGELOG
- Configuration file support (`~/.config/voiceforge/config.toml`)
- Custom exception hierarchy for consistent error handling
- GitHub Actions CI (lint, typecheck, test)
- Pre-commit hooks (ruff, trailing-whitespace, end-of-file-fixer)
- Progress indicators for long operations
- Shell completion documentation
- Dockerfile and docker-compose for reproducible GPU environments
- Engine instance caching to avoid reloading models
- Audio format conversion (mp3/flac/ogg auto-convert to WAV)
- `synth batch` command for multi-line text synthesis
- `voice export` / `voice import` commands
- Input validation for synth text, audio files, and emotion_alpha

### Changed
- `indextts` moved to optional dependency for portability
- Hardcoded fallback path replaced with `VOICEFORGE_INDEXTTS_ROOT` env var
- All internal exceptions use custom `VoiceForgeError` hierarchy

### Fixed
- `indextts` path in `pyproject.toml` was machine-specific and non-portable

## [0.1.0] - 2026-03-15

### Added
- Initial release with multi-engine voice cloning CLI
- IndexTTS-2 engine implementation
- Voice management commands (`voice list`, `voice info`)
- Profile extraction (`profile extract`, `profile info`)
- Speech synthesis (`synth`)
- Engine inspection (`engine list`, `engine info`)
- VoiceProfile v2 format with v1 backward compatibility
- Audio scanning and validation utilities
- Centralized logging with verbosity levels
- Development toolchain (ruff, mypy, pytest)
- Test suite with GPU-independent tests
