"""Load optional TOML configuration (stdlib :mod:`tomllib`, Python 3.11+)."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    """
    Data container for settings shared by CLI subcommands.
    
    Attributes:
        payday: The day of the month used for temporal analysis splits.
        default_csv: Path to a default CSV file if no source is provided.
    """

    payday: int = 15
    default_csv: str | None = None


def _overlay_from_file(cfg: AppConfig, path: Path) -> None:
    """
    Reads a TOML file and updates the AppConfig instance with found values.
    
    Args:
        cfg: The current AppConfig instance to modify in-place.
        path: The filesystem path to the TOML configuration file.
    """
    # Parse the TOML content into a dictionary
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    
    # Ensure the root of the TOML is a table/dictionary
    if not isinstance(raw, dict):
        return
        
    # Update payday if present in the file
    if "payday" in raw:
        cfg.payday = int(raw["payday"])
        
    # Update default_csv if present; ensures empty strings are treated as None
    if raw.get("default_csv"):
        cfg.default_csv = str(raw["default_csv"]).strip() or None


def _validate_payday(n: int) -> None:
    """
    Ensures the payday value falls within a valid calendar range (1-28).
    
    Raises:
        ValueError: If the payday is outside the allowed range.
    """
    if not 1 <= n <= 28:
        raise ValueError(f"payday must be between 1 and 28, got {n}")


def load_merged_config(*, explicit: Path | None = None) -> AppConfig:
    """
    Constructs the final AppConfig by merging multiple potential sources.
    
    The priority order for merging is:
    1. Default internal values (payday=15).
    2. 'analyzer.toml' located in the current working directory.
    3. The file path specified in the 'LL_ANALYZER_CONFIG' environment variable.
    
    If 'explicit' is provided, the merging logic is bypassed and only 
    that specific file is used.
    """
    cfg = AppConfig()
    
    # Handle the case where a specific config path is provided via CLI
    if explicit is not None:
        if not explicit.is_file():
            raise FileNotFoundError(f"Config file not found: {explicit}")
        _overlay_from_file(cfg, explicit)
        _validate_payday(cfg.payday)
        return cfg

    # 1. Attempt to load from a local 'analyzer.toml' file in the CWD
    local = Path.cwd() / "analyzer.toml"
    if local.is_file():
        _overlay_from_file(cfg, local)
        
    # 2. Attempt to load from a file path provided in environment variables
    env_path = (os.environ.get("LL_ANALYZER_CONFIG") or "").strip()
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_file():
            _overlay_from_file(cfg, p)

    # Final validation check after all overlays are applied
    _validate_payday(cfg.payday)
    
    return cfg