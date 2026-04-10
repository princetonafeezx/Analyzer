"""``ll-analyzer`` command-line interface (argparse subcommands)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

# Local imports for configuration management
from config import AppConfig, load_merged_config


def _cmd_version(_args: argparse.Namespace, _config: AppConfig) -> int:
    """
    Retrieves and prints the current version of the ll-analyzer package.
    Attempts to use metadata first, falling back to a local version file.
    """
    try:
        from importlib.metadata import version
        v = version("ll-analyzer")
    except Exception:
        # Fallback for development environments or manual installs
        from version import __version__ as v
    print(v)
    return 0


def _cmd_menu(_args: argparse.Namespace, config: AppConfig) -> int:
    """
    Launches the interactive terminal menu.
    Passes the current payday configuration as the starting default.
    """
    from menu import menu
    menu(initial_payday=config.payday)
    return 0


def _cmd_analyze(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Core command logic for the 'analyze' subcommand.
    Loads data, runs metrics calculations, and prints the report.
    """
    from csv_load import load_categorized_file
    from metrics import run_all_reports
    from mock_data import generate_mock_transactions
    from output import print_full_analysis

    # Enforce mutual exclusivity if not handled perfectly by parser groups
    if args.csv is not None and args.mock:
        print("error: use either --csv or --mock, not both.", file=sys.stderr)
        return 2

    records: list
    duplicate_records: list
    
    # Logic Branch 1: User provided a specific CSV file
    if args.csv is not None:
        records, warnings, duplicate_records = load_categorized_file(args.csv)
        for warning in warnings:
            print(warning, file=sys.stderr)
            
    # Logic Branch 2: User requested generated mock data
    elif args.mock:
        records = generate_mock_transactions()
        duplicate_records = []
        
    # Logic Branch 3: No CLI flags used, falling back to 'default_csv' in config
    elif config.default_csv:
        path = Path(config.default_csv)
        records, warnings, duplicate_records = load_categorized_file(path)
        for warning in warnings:
            print(warning, file=sys.stderr)
            
    # Error state: No data source provided anywhere
    else:
        print(
            "error: specify --csv or --mock, or set default_csv in analyzer.toml.",
            file=sys.stderr,
        )
        return 2

    # Process the loaded data and output the final report
    report = run_all_reports(records, payday_date=config.payday)
    print_full_analysis(report, duplicate_count=len(duplicate_records))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """
    Configures the ArgumentParser with global options and subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="ll-analyzer",
        description="Financial pattern detector — spending reports from categorized transactions.",
    )
    
    # Global options available before the subcommand
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

    # Initialize subcommands (menu, analyze, version)
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # 'menu' subcommand configuration
    p_menu = sub.add_parser("menu", help="Interactive text menu (default)")
    p_menu.set_defaults(func=_cmd_menu)

    # 'analyze' subcommand configuration with exclusive data source group
    p_an = sub.add_parser("analyze", help="Print full analysis report to stdout")
    g = p_an.add_mutually_exclusive_group()
    g.add_argument("--csv", type=Path, metavar="PATH", help="Categorized CSV file")
    g.add_argument("--mock", action="store_true", help="Use built-in mock transactions")
    p_an.set_defaults(func=_cmd_analyze)

    # 'version' subcommand configuration
    sub.add_parser("version", help="Print package version").set_defaults(func=_cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Main application entry point. Handles setup, config merging, and execution.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Step 1: Load and merge configuration from TOML/Env vars
    try:
        config = load_merged_config(explicit=args.config)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Step 2: Override config if --payday was passed directly to CLI
    if args.payday is not None:
        if not 1 <= args.payday <= 28:
            print("error: --payday must be between 1 and 28.", file=sys.stderr)
            return 1
        # Create a new config instance with the overridden payday
        config = AppConfig(payday=args.payday, default_csv=config.default_csv)

    # Step 3: Default to 'menu' if no command was specified
    if args.command is None:
        return _cmd_menu(args, config)

    # Step 4: Route execution to the function associated with the chosen command
    func: Callable[[argparse.Namespace, AppConfig], int] = args.func
    return func(args, config)


def entrypoint() -> None:
    """Standard entry point for console_scripts defined in setup/pyproject."""
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()