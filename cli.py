from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from config import AppConfig, load_merged_config


def _cmd_version(_args: argparse.Namespace, _config: AppConfig) -> int:
    try:
        from importlib.metadata import version

        v = version("ll-analyzer")
    except Exception:
        from version import __version__ as v
    print(v)
    return 0



def main(argv: list[str] | None = None) -> int:
    pass

if __name__ == "__main__":
    entrypoint()
