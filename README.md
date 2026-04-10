# Financial Pattern Detector (ll-analyzer)

Standalone app that analyzes **categorized transactions** and surfaces patterns: top merchants by frequency and spend, day-of-week and weekend vs weekday totals, pre/post payday splits, monthly totals with simple trends, and **anomalies** (amounts above **3× the category average**).

**Python:** 3.11+ (uses `tomllib` for optional config files.)

## Install

From the repository root:

```bash
pip install .
```

Editable install for development:

```bash
pip install -e ".[dev]"
```

This installs the **`ll-analyzer`** command and registers the `analysis` package (plus root modules such as `schemas`, `parsing`, …).

## Command-line interface

Global options (apply before the subcommand):

| Option | Description |
|--------|-------------|
| `--config PATH` | Use only this TOML file (see **Configuration**). |
| `--payday N` | Payday as day of month **1–28**; overrides the config file. |

Subcommands:

| Command | Description |
|---------|-------------|
| *(none)* | Same as `menu` — interactive text menu. |
| `menu` | Interactive menu: load CSV, mock data, run full or partial reports, set payday. |
| `analyze` | Print the **full** report to stdout (non-interactive). |
| `version` | Print the installed package version. |

`analyze` data source (pick one, or rely on config):

| Option | Description |
|--------|-------------|
| `--csv PATH` | Load a categorized CSV. |
| `--mock` | Use built-in mock transactions. |
| *(omit both)* | Uses `default_csv` from config if set; otherwise the command errors with a hint. |

Examples:

```bash
ll-analyzer version
ll-analyzer --payday 1 menu
ll-analyzer analyze --mock
ll-analyzer analyze --csv ./exports/categorized.csv
python -m analysis.cli analyze --mock
python -m analysis          # interactive menu; reads config for default payday
```

## Configuration

Optional **TOML** file: **`analyzer.toml`** in the current working directory. If the environment variable **`LL_ANALYZER_CONFIG`** is set to a file path, that file is loaded **after** `analyzer.toml` and overrides overlapping keys.

Supported keys:

```toml
# Day of month treated as payday for time-of-month split (1–28)
payday = 15

# Optional: default CSV for `ll-analyzer analyze` when --csv/--mock are omitted
# default_csv = "C:/path/to/categorized.csv"
```

Use **`analyzer.local.toml`** for machine-specific paths (gitignored); you can point **`LL_ANALYZER_CONFIG`** at it.

## Data directory

Persisted CSV/JSON/report paths use **`ANALYZER_DATA_DIR`** when set, otherwise **`./analyzer_data`** under the process working directory. See `storage.get_data_dir`.

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q
```

Dependencies are declared in **`pyproject.toml`**. **`requirements.txt`** mirrors them for environments that prefer a requirements file.

---

## Feature checklist (original brief)

**Frequency & spend**

- Top 10 merchants by transaction count (manual dict counts, no `collections.Counter`)
- Top 10 by total dollar spend
- Ranked tables with counts and formatted currency

**Temporal patterns**

- Day-of-week totals and averages (Monday–Sunday)
- Weekend vs weekday comparison (% difference)
- Time-of-month split relative to a configurable payday
- Per-month totals with simple up/down/flat trend labels

**Anomalies**

- Category averages from dict accumulators
- Flag transactions **> 3×** category average
- List merchant, amount, average, multiple; summary by category

**Data handling**

- Categorized CSV loading with column detection
- Six-month mock data
- Date/amount parsing with validation
- Duplicate detection via `(date, merchant, amount)` keys

**Implementation**

- Root modules (`parsing`, `categorizer`, `storage`, …) and an **`analysis`** package for metrics, I/O, and output formatters
- **`ll_analyzer_app`**: argparse CLI, TOML config, `ll-analyzer` entry point
- Tests: `pytest`; record shapes use `typing_extensions.NotRequired` where needed
