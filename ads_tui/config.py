"""
Configuration handling for ads-tui.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from platformdirs import PlatformDirs

APP_NAME = "ads-tui"
APP_AUTHOR = "ads-tui"

dirs = PlatformDirs(APP_NAME, APP_AUTHOR)

CONFIG_DIR = Path(dirs.user_config_dir)
CACHE_DIR = Path(dirs.user_cache_dir)
DATA_DIR = Path(dirs.user_data_dir)

CONFIG_FILE = CONFIG_DIR / "config.toml"
CACHE_DB = CACHE_DIR / "cache.sqlite"


DEFAULT_CONFIG = """
# ADS API token
token = ""

# Number of search results returned
results = 10

# Prefer arXiv PDFs over publisher PDFs
prefer_arxiv = true

# Cache lifetime in days
cache_days = 30

# Directory where PDFs are downloaded
download_dir = "~/Papers"

# Default bibliography file
default_bib = "~/Documents/references.bib"
""".strip()


@dataclass(slots=True)
class Config:
    token: str

    results: int = 10

    prefer_arxiv: bool = True

    cache_days: int = 30

    download_dir: Path = Path("~/Papers").expanduser()

    default_bib: Path = Path("~/Documents/references.bib").expanduser()


def ensure_directories() -> None:
    """Create required directories."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_default_config() -> None:
    """Write a default config file if none exists."""

    ensure_directories()

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(DEFAULT_CONFIG + "\n")


def _read_config_file() -> dict:
    if not CONFIG_FILE.exists():
        create_default_config()

    with CONFIG_FILE.open("rb") as f:
        return tomllib.load(f)


def load_config() -> Config:
    """
    Load configuration.

    Priority:

        1. ADS_API_TOKEN environment variable
        2. config.toml
    """

    ensure_directories()

    cfg = _read_config_file()

    token = os.environ.get("ADS_API_TOKEN") or cfg.get("token", "")

    return Config(
        token=token,
        results=int(cfg.get("results", 10)),
        prefer_arxiv=bool(cfg.get("prefer_arxiv", True)),
        cache_days=int(cfg.get("cache_days", 30)),
        download_dir=Path(cfg.get("download_dir", "~/Papers")).expanduser(),
        default_bib=Path(
            cfg.get("default_bib", "~/Documents/references.bib")
        ).expanduser(),
    )


def require_token(config: Config) -> None:
    """Raise an error if no ADS API token is configured."""

    if config.token:
        return

    raise RuntimeError(
        "\n"
        "No ADS API token found.\n\n"
        "Either:\n"
        "  export ADS_API_TOKEN=<token>\n\n"
        "or edit:\n"
        f"  {CONFIG_FILE}\n"
    )
