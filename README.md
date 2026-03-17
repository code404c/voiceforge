# VoiceForge

Voice cloning CLI tool with multi-engine support. Extract voice profiles from audio clips and synthesize speech with emotion control.

## Requirements

- Python 3.10+
- NVIDIA GPU with CUDA 12.x
- [uv](https://docs.astral.sh/uv/) package manager
- [IndexTTS-2](https://github.com/AnyaCoder/index-tts) model (for the `indextts2` engine)

## Installation

```bash
# Clone the repository
git clone https://github.com/ysnow/voiceforge.git
cd voiceforge

# Install core dependencies
uv sync

# Install with IndexTTS-2 engine support
uv sync --extra indextts

# Or install indextts from a local checkout
uv pip install -e /path/to/index-tts
```

### IndexTTS-2 Setup

The `indextts2` engine requires the IndexTTS-2 model and checkpoints. Configure the path using one of:

1. **Install the package** — `uv pip install -e /path/to/index-tts`
2. **Environment variable** — `export VOICEFORGE_INDEXTTS_ROOT=/path/to/index-tts`
3. **Config file** — set `indextts_root` in `~/.config/voiceforge/config.toml`

The model expects `checkpoints/config.yaml` and `checkpoints/` directory inside the IndexTTS root.

## Quick Start

```bash
# 1. Create a voice directory and add audio clips (WAV, 3-15 seconds each)
mkdir -p ~/.local/share/voiceforge/voices/alice/clips
cp /path/to/alice_*.wav ~/.local/share/voiceforge/voices/alice/clips/

# 2. Extract a voice profile
voiceforge profile extract --voice alice

# 3. Synthesize speech
voiceforge synth --voice alice --text "Hello, this is a test." --output hello.wav

# With emotion control
voiceforge synth --voice alice \
  --text "I'm so happy to see you!" \
  --emotion-text "excited and joyful" \
  --emotion-alpha 0.8 \
  --output happy.wav
```

## CLI Reference

### Voice Management

```bash
voiceforge voice list              # List all voices with clip counts and profile status
voiceforge voice info <name>       # Show detailed info (clips, durations, profiles)
```

### Profile Extraction

```bash
voiceforge profile extract -v <voice> [-e <engine>]   # Extract voice profile from clips
voiceforge profile info -v <voice> [-e <engine>]       # Show profile metadata and tensor shapes
```

### Speech Synthesis

```bash
voiceforge synth -v <voice> -t <text> -o <output.wav> [-e <engine>]
  --emotion-text <text>     # Optional: text for emotion detection
  --emotion-alpha <0-1>     # Optional: emotion blending strength (default: 1.0)

voiceforge synth batch -v <voice> -i <input.txt> -o <output_dir>  # Batch synthesis
```

### Engine Inspection

```bash
voiceforge engine list             # Show all registered engines
voiceforge engine info <name>      # Show engine details (version, class path)
```

### Configuration

```bash
voiceforge config show             # Display current configuration and sources
voiceforge config init             # Create a default config file
```

### Global Options

```bash
voiceforge --version / -V          # Show version
voiceforge -v                      # INFO log level
voiceforge -vv                     # DEBUG log level
```

## Configuration

VoiceForge reads configuration from (highest to lowest priority):

1. CLI flags
2. Environment variables
3. Config file (`~/.config/voiceforge/config.toml`)
4. Built-in defaults

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VOICEFORGE_VOICES_DIR` | Voice data directory | `~/.local/share/voiceforge/voices` |
| `VOICEFORGE_INDEXTTS_ROOT` | IndexTTS-2 repo path | Auto-detected from package |
| `VOICEFORGE_DEFAULT_ENGINE` | Default TTS engine | `indextts2` |

### Config File

```toml
# ~/.config/voiceforge/config.toml
voices_dir = "~/.local/share/voiceforge/voices"
default_engine = "indextts2"
indextts_root = "/path/to/index-tts"
```

## Project Structure

```
src/voiceforge/
├── __init__.py              # Package root, __version__
├── config.py                # Path resolution and configuration
├── exceptions.py            # Custom exception hierarchy
├── logging.py               # Centralized logging setup
├── cli/
│   ├── app.py               # Main CLI entry point (Typer)
│   ├── voice_cmd.py         # voice list / info
│   ├── profile_cmd.py       # profile extract / info
│   ├── synth_cmd.py         # synth (single + batch)
│   └── engine_cmd.py        # engine list / info
├── engine/
│   ├── base.py              # TTSEngine ABC, ProfileData, EngineInfo
│   ├── registry.py          # Engine registration and discovery
│   └── indextts2.py         # IndexTTS-2 implementation
├── audio/
│   └── utils.py             # Audio scanning, validation, format conversion
└── profile/
    └── schema.py            # VoiceProfile dataclass with v1/v2 compat
```

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run checks
make check          # lint + typecheck + test
make lint           # ruff check
make format         # ruff format + fix
make typecheck      # mypy
make test           # pytest (non-GPU)
make test-cov       # pytest with coverage report

# Pre-commit hooks
pre-commit install
```

## Shell Completion

Typer supports shell completion out of the box:

```bash
# Install completion for your shell
voiceforge --install-completion

# Generate completion script without installing
voiceforge --show-completion
```

## Known Limitations

- Only WAV audio input is supported (mp3/flac/ogg auto-converted if ffmpeg available)
- IndexTTS-2 clips should be 3-15 seconds for best results
- GPU with sufficient VRAM required (8GB+ recommended)
- Single-engine inference only (no multi-GPU parallelism)

## License

[MIT](LICENSE)
