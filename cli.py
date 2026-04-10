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

def _cmd_menu(_args: argparse.Namespace, config: AppConfig) -> int:
    from menu import menu

    menu(initial_payday=config.payday)
    return 0

def _cmd_analyze(args: argparse.Namespace, config: AppConfig) -> int:
    from csv_load import load_categorized_file
    from metrics import run_all_reports
    from mock_data import generate_mock_transactions
    from output import print_full_analysis

    if args.csv is not None and args.mock:
        print("error: use either --csv or --mock, not both.", file=sys.stderr)
        return 2

    records: list
    duplicate_records: list
    if args.csv is not None:
        records, warnings, duplicate_records = load_categorized_file(args.csv)
        for warning in warnings:
            print(warning, file=sys.stderr)
    elif args.mock:
        records = generate_mock_transactions()
        duplicate_records = []
    elif config.default_csv:
        path = Path(config.default_csv)
        records, warnings, duplicate_records = load_categorized_file(path)
        for warning in warnings:
            print(warning, file=sys.stderr)
    else:
        print(
            "error: specify --csv or --mock, or set default_csv in analyzer.toml.",
            file=sys.stderr,
        )
        return 2

    report = run_all_reports(records, payday_date=config.payday)
    print_full_analysis(report, duplicate_count=len(duplicate_records))
    return 0

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ll-analyzer",
        description="Financial pattern detector — spending reports from categorized transactions.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        metavar="PATH",
        help="TOML config file (if omitted: ./analyzer.toml then $LL_ANALYZER_CONFIG)",
    )
    parser.add_argument(
        "--payday",
        type=int,
        metavar="N",
        help="Payday as day of month 1–28 (overrides config file)",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p_menu = sub.add_parser("menu", help="Interactive text menu (default)")
    p_menu.set_defaults(func=_cmd_menu)

    p_an = sub.add_parser("analyze", help="Print full analysis report to stdout")
    g = p_an.add_mutually_exclusive_group()
    g.add_argument("--csv", type=Path, metavar="PATH", help="Categorized CSV file")
    g.add_argument("--mock", action="store_true", help="Use built-in mock transactions")
    p_an.set_defaults(func=_cmd_analyze)

    sub.add_parser("version", help="Print package version").set_defaults(func=_cmd_version)

    return parser






















def main(argv: list[str] | None = None) -> int:
    pass

if __name__ == "__main__":
    entrypoint()
