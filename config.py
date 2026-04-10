from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    payday: int = 15
    default_csv: str | None = None

def _overlay_from_file(cfg: AppConfig, path: Path) -> None:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return
    if "payday" in raw:
        cfg.payday = int(raw["payday"])
    if raw.get("default_csv"):
        cfg.default_csv = str(raw["default_csv"]).strip() or None

def _validate_payday(n: int) -> None:
    if not 1 <= n <= 28:
        raise ValueError(f"payday must be between 1 and 28, got {n}")

def load_merged_config(*, explicit: Path | None = None) -> AppConfig:
    cfg = AppConfig()
    if explicit is not None:
        if not explicit.is_file():
            raise FileNotFoundError(f"Config file not found: {explicit}")
        _overlay_from_file(cfg, explicit)
        _validate_payday(cfg.payday)
        return cfg

    local = Path.cwd() / "analyzer.toml"
    if local.is_file():
        _overlay_from_file(cfg, local)
    env_path = (os.environ.get("LL_ANALYZER_CONFIG") or "").strip()
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_file():
            _overlay_from_file(cfg, p)

    _validate_payday(cfg.payday)
    return cfg