from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    payday: int = 15
    default_csv: str | None = None


