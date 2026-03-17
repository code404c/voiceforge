"""Configuration display and initialization commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from voiceforge.config import CONFIG_DIR, CONFIG_FILE, DEFAULT_ENGINE, VOICES_DIR, get_config

app = typer.Typer(no_args_is_help=True)
console = Console()

_DEFAULT_CONFIG = """\
# VoiceForge configuration
# See: voiceforge config show

# voices_dir = "~/.local/share/voiceforge/voices"
# default_engine = "indextts2"
# indextts_root = "/path/to/index-tts"
"""


@app.command("show")
def config_show() -> None:
    """Display current configuration and sources."""
    cfg = get_config()

    table = Table(title="VoiceForge Configuration")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_column("Source", style="dim")

    import os

    # voices_dir
    env_v = os.environ.get("VOICEFORGE_VOICES_DIR")
    source = "env" if env_v else ("config" if CONFIG_FILE.is_file() else "default")
    table.add_row("voices_dir", str(VOICES_DIR), source)

    # default_engine
    env_e = os.environ.get("VOICEFORGE_DEFAULT_ENGINE")
    source = "env" if env_e else ("config" if CONFIG_FILE.is_file() else "default")
    table.add_row("default_engine", DEFAULT_ENGINE, source)

    # indextts_root
    env_i = os.environ.get("VOICEFORGE_INDEXTTS_ROOT")
    source = "env" if env_i else ("config" if cfg.indextts_root else "auto")
    table.add_row("indextts_root", cfg.indextts_root or "[dim]auto-detect[/dim]", source)

    console.print(table)
    console.print(f"\n[dim]Config file: {CONFIG_FILE}[/dim]")


@app.command("init")
def config_init() -> None:
    """Create a default config file at ~/.config/voiceforge/config.toml."""
    if CONFIG_FILE.exists():
        console.print(f"[yellow]Config file already exists: {CONFIG_FILE}[/yellow]")
        raise typer.Exit()

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(_DEFAULT_CONFIG)
    console.print(f"[green]Config file created: {CONFIG_FILE}[/green]")
