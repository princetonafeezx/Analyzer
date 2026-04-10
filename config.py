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

