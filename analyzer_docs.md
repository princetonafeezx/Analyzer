# Architecture Decision Record
## App 13 — Analyzer
**Ledger Logic Group | Document 1 of 5**
**Status: Accepted**

---

## Context

The Analyzer is the thirteenth app in the portfolio and the sixth in the Ledger Logic group. It takes categorized transaction records (produced by the Categorizer, App 11) and computes spending patterns: top merchants by frequency and spend, day-of-week breakdown, weekend vs weekday averages, pre/post-payday spending split, monthly trends with trend direction, and anomaly detection (3× category average threshold). The Analyzer is the most fully-featured standalone module in the portfolio — it has its own TOML config, argparse CLI with subcommands, a `records.py` validation layer, and a `mock_data.py` generator producing six months of repeatable data.

---

## Decisions

### Decision 1 — Manual dict counts instead of `collections.Counter`

**Chosen:** `count_by_merchant()` and `spend_by_merchant()` use plain `dict` with `.get(key, 0)` accumulation. `group_category_averages()` also uses plain dicts.

**Rejected:** `from collections import Counter; Counter(...)`.

**Reason:** This is the deliberate learning exercise noted in the `metrics.py` module docstring. `Counter` would produce identical results with less code, but the manual dict approach forces explicit understanding of what accumulation means: initialize a default, iterate, increment, sort. The README acknowledges this as a deliberate choice and not an oversight.

---

### Decision 2 — `records.py` as a strict validation layer

**Chosen:** `normalize_analysis_record()` validates each incoming dict against strict type and value rules: required fields `date` and `amount`, `bool`-before-numeric type guard, `math.isnan/isinf` check for non-finite amounts, date coercion via `parse_date()`. `coerce_analysis_records()` applies it to a sequence and raises `ValueError` with the index of the first bad row.

**Rejected:** Accepting records as-is and handling errors per-metric.

**Reason:** Metric functions should operate on clean data. If a bad record slips through to `day_of_week_breakdown()`, it causes a confusing error inside the metric, not at the boundary. The validation layer makes the contract explicit: all records entering `run_all_reports()` have been validated. The `bool`-before-numeric guard prevents `True` from being coerced to `1.0` — the same pattern established in App 10 (Investment Engine).

---

### Decision 3 — `AppConfig` as a stdlib `@dataclass` loaded from TOML

**Chosen:** `AppConfig(payday: int = 15, default_csv: str | None = None)` is a stdlib `@dataclass`. `load_merged_config()` reads from `analyzer.toml` (CWD), then from `LL_ANALYZER_CONFIG` environment variable. CLI `--payday` overrides the config. Python 3.11 `tomllib` is the parser.

**Rejected:** Command-line arguments only (no persistence).

**Reason:** `payday` is a user preference that should persist across sessions. A CWD `analyzer.toml` is the standard project-scoped config pattern. The environment variable override supports CI environments. The merge order (default → CWD file → env file → CLI flag) follows the conventional precedence: more specific overrides less specific.

---

### Decision 4 — `run_all_reports()` as the single bundled entry point

**Chosen:** `run_all_reports(records, payday_date)` calls all seven metric functions and returns a single `AnalysisReport` TypedDict. The CLI `analyze` subcommand calls it once and passes the result to `print_full_analysis()`.

**Rejected:** Separate CLI calls for each metric.

**Reason:** The `AnalysisReport` dict is the complete picture of the data. Computing all metrics together means a single load, a single `coerce_analysis_records()` pass, and a single output call. Individual metrics are still callable directly (the menu's "individual report" option calls them), but the primary path is the bundled report.

---

### Decision 5 — Anomaly detection at 3× category average

**Chosen:** `detect_anomalies()` flags any transaction where `amount > category_average × 3`. The threshold is hardcoded.

**Rejected:** A configurable threshold or a statistical (z-score) approach.

**Reason:** The 3× rule is a simple, human-understandable heuristic. A one-time large purchase (hotel, emergency repair) is likely 3× the monthly average for its category. Z-score anomaly detection would require normally distributed data and at least ~30 samples per category — neither of which is guaranteed for monthly transaction data. The hardcoded threshold is a learning exercise in iterative aggregation; making it configurable is the noted next refactor.

---

### Decision 6 — `mock_data.py` produces six months of repeatable data with intentional anomalies

**Chosen:** `generate_mock_transactions()` generates 6 months of fixed template transactions with: seasonal amount variation (`amount + (month % 3) × 1.15`), a planted anomaly (Amazon $420.00 in month offset 2, normally ~$64-67), and a duplicate pair (two identical Starbucks entries in month offset 1).

**Rejected:** Random or purely sequential mock data.

**Reason:** Repeatable mock data makes the anomaly detection and duplicate detection demonstrably functional. The $420 Amazon entry is approximately 6× the normal category average, guaranteeing it appears in the anomaly report. The duplicate Starbucks entries test the duplicate detection in `csv_load.py`. The month-offset approach ensures the monthly trends always span a real calendar range relative to today.

---

### Decision 7 — `cli.py` with `set_defaults(func=...)` dispatch

**Chosen:** Each subparser calls `p_an.set_defaults(func=_cmd_analyze)`. `main()` routes execution with `func = args.func; return func(args, config)`. Default command (no subcommand) falls through to `_cmd_menu`.

**Rejected:** A chained `if args.command == "analyze": ...` in `main()`.

**Reason:** The `set_defaults(func=...)` pattern is the standard argparse dispatch idiom. Adding a new subcommand requires one parser definition and one `set_defaults` call — no changes to the main dispatch block. The pattern was established in earlier Ledger Logic modules and reaches its cleanest form here with three subcommands (menu, analyze, version).

---

## Consequences

**Positive:**
- `records.py` validation layer catches bad data at the boundary, not inside metric functions.
- Manual dict counts demonstrate understanding of what `Counter` abstracts.
- TOML config with environment variable override supports both local and CI use.
- Planted anomaly and duplicate in mock data make features demonstrable without real data.
- `set_defaults(func=...)` dispatch scales cleanly to additional subcommands.

**Negative / Trade-offs:**
- `tomllib` is Python 3.11+. On 3.10 the import fails. The module requires 3.11 for the `config.py` to work. This is a version constraint not present in other Ledger Logic apps.
- Anomaly threshold (3×) is hardcoded. It cannot be tuned without code changes.
- `coerce_analysis_records()` raises on the first bad row (fail-fast). For large files with scattered bad rows, this prevents partial reporting.

---

*Constitution reference: Articles 1, 2, 3. Amendment 1.3: `parsing.py`, `schemas.py`, `storage.py` are pinned snapshots. Deliberate learning exercise noted: manual dict counts.*


---


# Technical Design Document
## App 13 — Analyzer
**Ledger Logic Group | Document 2 of 5**

---

## Overview

The Analyzer computes spending patterns from categorized transaction records. It has eight metrics, a validation layer, a TOML config system, argparse subcommands, six-month repeatable mock data, and a full print-formatted output layer.

**Files:** `metrics.py` (core analysis), `records.py` (validation), `csv_load.py` (file loading + duplicate detection), `mock_data.py` (synthetic data), `output.py` (print formatting), `cli.py` (argparse entry point), `menu.py` (interactive menu), `config.py` (TOML config), `csv_columns.py` (column detection), `categorizer.py` (borrowed from App 11), `textutil.py`, `version.py`
**Shared (pinned snapshots):** `parsing.py`, `schemas.py`, `storage.py`
**Entry points:** `cli.main()` → `_cmd_analyze()` or `_cmd_menu()`, or `menu.main()`
**Dependencies:** `csv`, `argparse`, `tomllib`, `dataclasses`, `math`, `datetime`, `re` (stdlib); shared Ledger Logic modules

---

## Module Responsibilities

| File | Responsibility |
|---|---|
| `metrics.py` | Eight metric functions + `run_all_reports()` |
| `records.py` | `normalize_analysis_record()`, `coerce_analysis_records()` |
| `csv_load.py` | Load CSV + deduplicate on `(date, merchant, amount)` |
| `mock_data.py` | Six-month mock data with planted anomaly and duplicates |
| `output.py` | Print-formatted tables for each report section |
| `cli.py` | Argparse entry point: `menu`, `analyze`, `version` subcommands |
| `menu.py` | Interactive text menu |
| `config.py` | TOML config loading with env-var override |
| `csv_columns.py` | Five-role column detection (date, merchant, amount, category, subcategory) |
| `categorizer.py` | Borrowed from App 11 (for mock data categorization in `mock_data.py`) |

---

## Data Flow

```
CSV file or mock data
        │
        ▼
csv_load.load_categorized_file(path)
        ├─ detect_columns(headers) → {date, merchant, amount, category, subcategory}
        ├─ For each row: parse_date + parse_amount + normalize_analysis_record
        └─ Duplicate detection: (date_str, merchant.lower(), round(amount,2)) → seen set
        │
        ▼
list[CategorizedRecord], warnings, duplicates
        │
        ▼
metrics.run_all_reports(records, payday_date)
        ├─ coerce_analysis_records(records) → validated list
        ├─ count_by_merchant()      → list[MerchantFrequencySummaryRow]  (manual dict)
        ├─ spend_by_merchant()      → list[MerchantSpendSummaryRow]      (manual dict)
        ├─ day_of_week_breakdown()  → list[DayOfWeekSpendRow]
        ├─ weekend_vs_weekday()     → WeekendWeekdaySummary
        ├─ time_of_month_analysis() → TimeOfMonthSplit
        ├─ monthly_trends()         → list[MonthlyTrendRow]
        └─ detect_anomalies()       → AnomalyReport
        │
        ▼
AnalysisReport
        │
        ▼
output.print_full_analysis(report, duplicate_count)
```

---

## `records.py` Validation

### `normalize_analysis_record(raw) → CategorizedRecord`
Validation sequence:
1. `date` key present → already `date` object or `parse_date(str(d_raw))`
2. `amount` key present
3. `type(amt_raw) is bool` → raise (before numeric check)
4. `isinstance(amt_raw, (int, float))` → `float(amt_raw)` else `parse_amount(str(amt_raw))`
5. `math.isnan(amount) or math.isinf(amount)` → raise
6. `merchant` → `str(...).strip()`, default `""`
7. `category` → `str(...).strip() or "Unknown"`
8. `subcategory` → `str(...).strip() or category`

### `coerce_analysis_records(records) → list[CategorizedRecord]`
Applies `normalize_analysis_record()` to every row. Raises `ValueError(f"Invalid record at index {i}: {exc}")` on first failure.

---

## `csv_columns.py` — Five-Role Scorer

Detects five columns: `date`, `merchant`, `amount`, `category`, `subcategory`. Each role has a dedicated scorer with additive keyword weights and token-set matching. Key distinctions:
- `_score_subcategory()` checks for "sub" + "category" tokens and has higher minimum score (9.0) to prevent accidental overlap with category column
- `_score_category()` yields to subcategory — if a column scores ≥10 for subcategory, it scores 0 for category
- Fallback: if a role is not detected, uses positional defaults (date=col0, merchant=col1, amount=col2, category=col3)

---

## Eight Metrics

### `count_by_merchant(records) → list[MerchantFrequencySummaryRow]`
Manual dict: `counts[merchant] = counts.get(merchant, 0) + 1`. Sorts by `(-count, merchant)`. Returns top 10.

### `spend_by_merchant(records) → list[MerchantSpendSummaryRow]`
Manual dict: `totals[merchant] = totals.get(merchant, 0.0) + amount`. Sorts by `(-total, merchant)`. Returns top 10.

### `day_of_week_breakdown(records) → list[DayOfWeekSpendRow]`
Iterates records, maps `date.weekday()` → `DAY_NAMES` index. Returns all 7 days in order.

### `weekend_vs_weekday(records) → WeekendWeekdaySummary`
`weekday() >= 5` → weekend. Computes totals, averages, and `percentage_difference = (weekend_avg - weekday_avg) / weekday_avg × 100`.

### `time_of_month_analysis(records, payday_date=15) → TimeOfMonthSplit`
`d.day < payday_date` → pre-payday. Returns pre/post totals and counts.

### `monthly_trends(records) → list[MonthlyTrendRow]`
Groups by `d.strftime("%Y-%m")`. Sorts chronologically. Labels: first row `"starting point"`, then `"up"`, `"down"`, or `"flat"` by comparing to previous total.

### `detect_anomalies(records) → AnomalyReport`
Two-pass: first `group_category_averages()` computes `{category: {total, count, average}}`. Second pass flags `amount > average × 3`. Sorts by `(-multiple, -amount)`.

### `run_all_reports(records, payday_date=15) → AnalysisReport`
Calls `coerce_analysis_records()` then all seven metric functions.

---

## Config System: `config.py`

### Load order

```
AppConfig(payday=15, default_csv=None)   ← defaults
    │
    ▼
CWD / analyzer.toml                      ← local project config
    │
    ▼
$LL_ANALYZER_CONFIG                      ← environment variable path
    │
    ▼
--payday CLI flag                         ← highest priority
```

### `AppConfig`
```python
@dataclass
class AppConfig:
    payday: int = 15
    default_csv: str | None = None
```

`_validate_payday()` enforces `1 ≤ payday ≤ 28` after all overlays.

---

## Mock Data: `mock_data.py`

`generate_mock_transactions()` generates 13 template transactions × 6 months = 78 rows, plus:
- **Anomaly** (offset 2, month-3-back): Amazon Marketplace `$420.00` (normally ~$64–67) — ~6× category average
- **Duplicates** (offset 1, month-2-back): Two identical Starbucks `$7.45` entries

Seasonal variation: `adjusted_amount = base_amount + (month % 3) × 1.15`

---

## Duplicate Detection: `csv_load.py`

Key: `(parsed_date.isoformat(), merchant.lower(), round(amount, 2))`

First occurrence → `records`. Subsequent occurrences → `duplicates`. Both lists returned. `print_full_analysis()` receives `duplicate_count = len(duplicates)`.


---


# Interface Design Specification
## App 13 — Analyzer
**Ledger Logic Group | Document 3 of 5**

---

## Public API

### Primary Entry Point

```python
run_all_reports(
    records: Sequence[Mapping[str, Any]],
    payday_date: int = 15,
) -> AnalysisReport
```

---

### Individual Metrics

```python
count_by_merchant(records) -> list[MerchantFrequencySummaryRow]
spend_by_merchant(records) -> list[MerchantSpendSummaryRow]
day_of_week_breakdown(records) -> list[DayOfWeekSpendRow]
weekend_vs_weekday(records) -> WeekendWeekdaySummary
time_of_month_analysis(records, payday_date=15) -> TimeOfMonthSplit
monthly_trends(records) -> list[MonthlyTrendRow]
detect_anomalies(records) -> AnomalyReport
```

---

### File Loading

```python
# csv_load.py
load_categorized_file(file_path: str | Path) -> tuple[list[CategorizedRecord], list[str], list[CategorizedRecord]]
# Returns: (records, warnings, duplicates)
```

---

### CLI

```bash
# Interactive menu (default when no subcommand)
ll-analyzer
python cli.py

# Full analysis from CSV
ll-analyzer analyze --csv categorized_transactions.csv
python cli.py analyze --csv categorized_transactions.csv

# Analysis from mock data
ll-analyzer analyze --mock
python cli.py analyze --mock

# Override payday
ll-analyzer analyze --csv data.csv --payday 1

# Custom config file
ll-analyzer --config my_config.toml analyze --csv data.csv

# Print version
ll-analyzer version
```

---

## `AnalysisReport` Schema

```python
{
    "record_count": int,
    "top_by_frequency": list[MerchantFrequencySummaryRow],
    "top_by_spend": list[MerchantSpendSummaryRow],
    "day_of_week": list[DayOfWeekSpendRow],
    "weekend_vs_weekday": WeekendWeekdaySummary,
    "time_of_month": TimeOfMonthSplit,
    "monthly_trends": list[MonthlyTrendRow],
    "anomaly_report": AnomalyReport,
}
```

---

## `analyzer.toml` Config Format

```toml
payday = 1
default_csv = "/path/to/categorized_transactions.csv"
```

Environment variable: `LL_ANALYZER_CONFIG=/path/to/custom.toml`

---

## Input/Output Examples

### Basic analysis from records
```python
from metrics import run_all_reports
from mock_data import generate_mock_transactions

records = generate_mock_transactions()
report = run_all_reports(records, payday_date=15)

print(f"Record count: {report['record_count']}")
print(f"Top merchant: {report['top_by_frequency'][0]['merchant']}")
print(f"Anomalies: {len(report['anomaly_report']['anomalies'])}")
```

### Access monthly trends
```python
for row in report["monthly_trends"]:
    print(f"{row['month']}: ${row['total']:.2f} ({row['trend']})")
# 2025-11: $1,850.23 (starting point)
# 2025-12: $1,921.45 (up)
# 2026-01: $1,798.12 (down)
```

### Check anomalies
```python
for row in report["anomaly_report"]["anomalies"]:
    print(f"{row['date']} {row['merchant']}: ${row['amount']:.2f} "
          f"({row['multiple']:.1f}× avg ${row['category_average']:.2f})")
# 2026-03-12 Amazon Marketplace: $420.00 (6.2× avg $67.79)
```

### Load categorized CSV
```python
from csv_load import load_categorized_file

records, warnings, duplicates = load_categorized_file("categorized.csv")
print(f"Loaded: {len(records)}, Duplicates skipped: {len(duplicates)}")
for warning in warnings:
    print(f"Warning: {warning}")
```

---

## CLI Output Format

```
Top merchants by frequency
Rank  Merchant                       Count
------------------------------------------
1     Starbucks                          12
2     Whole Foods                         6
...

Top merchants by spend
Rank  Merchant                       Total
------------------------------------------------
1     Landlord Portal              $8,700.00
...

Day-of-week breakdown
Day          Count           Total         Average
----------------------------------------------------
Monday           8        $643.23         $80.40
...

Weekend vs weekday average spend: $84.20 vs $71.45 (17.8% difference)
Time of month split: pre-payday $3,420.55 vs post-payday $5,123.88

Monthly trend tracking
Month           Total Spend       Trend
----------------------------------------
2025-11        $1,850.23  starting point
2025-12        $1,921.45          up
2026-01        $1,798.12        down
...

Anomalies
Date        Merchant                 Amount          Avg     X Over
------------------------------------------------------------------------
2026-03-12  Amazon Marketplace     $420.00       $67.79       6.19

Affected categories: Shopping

Duplicate transactions skipped during load: 2
```


---


# Runbook
## App 13 — Analyzer
**Ledger Logic Group | Document 4 of 5**

---

## Requirements

- Python 3.11 or later (`tomllib` is 3.11+)
- No third-party dependencies
- All module files in same directory or on `PYTHONPATH`
- `typing_extensions` for `schemas.py` (Python < 3.11 NotRequired)

---

## Installation

```bash
git clone https://github.com/PrincetonAfeez/ledger-logic
cd ledger-logic/analyzer
```

No `pip install` required for basic use.

For `ll-analyzer` console script:
```bash
pip install -e .
ll-analyzer version
```

---

## Quick Start

```bash
# Run with mock data (no CSV needed)
python cli.py analyze --mock

# Interactive menu
python cli.py

# Or via menu.py directly
python menu.py
```

---

## Common Workflows

### Analyze a categorized CSV
```bash
python cli.py analyze --csv ledgerlogic_data/categorized_transactions.csv
```

### Set payday day-of-month
```bash
# Via CLI flag
python cli.py analyze --csv data.csv --payday 1

# Via config file (persists)
echo 'payday = 1' > analyzer.toml
python cli.py analyze --csv data.csv
```

### Set default CSV path in config
```toml
# analyzer.toml
payday = 15
default_csv = "/home/user/data/categorized.csv"
```

```bash
# Now no --csv needed
python cli.py analyze
```

### Individual report from interactive menu
```
> python cli.py
Financial Pattern Detector
2. Run individual report
a. Top 10 by frequency
b. Top 10 by total spend
c. Day-of-week
d. Monthly trends
e. Anomalies
```

---

## Using as a Library

### Run all metrics
```python
from metrics import run_all_reports
from mock_data import generate_mock_transactions

report = run_all_reports(generate_mock_transactions(), payday_date=15)
```

### Run individual metric
```python
from metrics import detect_anomalies, count_by_merchant
from records import coerce_analysis_records
from mock_data import generate_mock_transactions

records = coerce_analysis_records(generate_mock_transactions())
anomalies = detect_anomalies(records)
top_freq = count_by_merchant(records)
```

### Validate a record
```python
from records import normalize_analysis_record

try:
    record = normalize_analysis_record({
        "date": "2026-01-15",
        "merchant": "Whole Foods",
        "amount": "84.20",
        "category": "Food & Drink",
    })
except ValueError as e:
    print(f"Bad record: {e}")
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'tomllib'`
`config.py` uses `tomllib` which is stdlib only in Python 3.11+. On 3.10, install `tomli`: `pip install tomli` and change `import tomllib` to `import tomli as tomllib`.

### `Invalid record at index N: missing required field 'date'`
The CSV column mapping may have failed. Check column headers against: `date/posted/transaction date`, `merchant/description/payee`, `amount/debit/credit`. Run `detect_columns()` manually to inspect the mapping.

### No anomalies reported despite obvious outliers
The threshold is `amount > category_average × 3`. If a category has only 1 transaction, its average equals its amount and no anomaly is ever triggered (the average *is* the amount). More transactions per category improve anomaly sensitivity.

### Monthly trends show only 1–2 months
The mock data covers 6 months from today backward. Real CSV data may span fewer months. Check `date` column format — if dates are not parsed correctly, they may all map to the same month key.


---


# Lessons Learned
## App 13 — Analyzer
**Ledger Logic Group | Document 5 of 5**

---

## Why This Design Was Chosen

The decision to use manual dict counts instead of `Counter` was the most intentional learning choice in the module. `Counter` is one of the most common Python stdlib patterns — it reduces `count_by_merchant()` to two lines. But writing the explicit accumulation loop makes the algorithm transparent: initialize the key, iterate, increment. The README documents this as deliberate. The lesson is that understanding what `Counter` does is more valuable at this stage than the convenience of using it.

The validation layer in `records.py` came from a failure in the first version of `metrics.py`. The initial `day_of_week_breakdown()` received raw dict records directly and crashed with an unhandled `AttributeError` when `record["date"]` was a string that `date.weekday()` could not be called on. Moving validation to a boundary layer — `coerce_analysis_records()` before any metrics run — produced clear error messages at the input rather than confusing failures inside calculations.

The TOML config was added because the `payday_date` parameter became awkward to pass through every function call. A project-scoped `analyzer.toml` with a `payday = 1` entry is the correct answer to "why does my time-of-month analysis always use the 15th?" — the user sets it once and forgets it.

---

## What Was Intentionally Omitted

**Savings rate and net income analysis:** The module analyzes spending but not savings. Net income (income minus expenses) and savings rate (net / gross) require knowing which transactions are income — the `Income` category from the Categorizer. Adding an income filter to `run_all_reports()` would enable this.

**Category-level spending breakdown:** The Categorizer produces `category` and `subcategory` fields. The Analyzer computes merchant-level stats but not category-level totals (total on Food & Drink, total on Housing, etc.). `categorizer.summarize_categories()` already does this — calling it inside `run_all_reports()` would be a one-line addition.

**Configurable anomaly threshold:** The 3× multiplier is hardcoded. Adding `anomaly_threshold: float = 3.0` to `AppConfig` and passing it through `run_all_reports()` to `detect_anomalies()` is a direct improvement.

**Export to file:** The `analyze` subcommand prints to stdout only. An `--output` flag writing the report to a text file via `write_text_report()` from `storage.py` would complete the pattern established by other Ledger Logic modules.

---

## Biggest Weakness

`coerce_analysis_records()` is fail-fast — it raises on the first invalid record and does not report how many records would have failed. For a production tool, fail-fast is correct for strict validation. But for a file with 1,000 rows where rows 3, 47, and 512 have bad amounts, fail-fast requires the user to fix one error, re-run, find the next, repeat. A fail-soft mode that collects all errors and returns `(valid_records, errors)` would be more usable for data-cleaning workflows.

---

## Scaling Considerations

**If transaction history grows to years of data:** `monthly_trends()` aggregates all months in one pass — it scales linearly. `detect_anomalies()` computes per-category averages in two passes — it also scales linearly. No algorithmic changes needed. The output table widths may need adjustment for 24+ months of trend data.

**If category analysis is needed:** Add `category_totals()` calling `categorizer.summarize_categories()` inside `run_all_reports()` and `print_category_totals()` in `output.py`. No structural changes.

**If configurable anomaly threshold is needed:** Add `anomaly_threshold: float = 3.0` to `AppConfig`, thread it through `run_all_reports(records, payday_date, anomaly_threshold)` → `detect_anomalies(records, threshold)`. One parameter addition, one usage update.

---

## What the Next Refactor Would Be

1. **Fail-soft record validation** — `coerce_analysis_records()` returns `(records, errors)` rather than raising on first failure.
2. **Configurable anomaly threshold** — `AppConfig.anomaly_threshold` with TOML and CLI support.
3. **Category summary in full report** — add `categorizer.summarize_categories(records)` to `AnalysisReport`.
4. **`--output` flag** — write report to file via `write_text_report()`.
5. **Python 3.10 compatibility** — add `tomli` fallback for `tomllib`.

---

## What This Project Taught

**Manual dict accumulation is pedagogically correct.** Writing the accumulation loop explicitly — `counts[key] = counts.get(key, 0) + 1` — makes the algorithm readable at the expense of brevity. Every Python developer should understand this pattern before using `Counter`. Writing it manually here enforced that understanding. The decision to document it in the module docstring as intentional rather than hiding it is the correct intellectual honesty move.

**A validation boundary layer prevents confusing errors.** The transition from raw dicts → validated `CategorizedRecord` objects in `records.py` means every metric function can assume its input is clean. The alternative — defensive try/except in every metric — produces inconsistent error handling and makes it unclear which records failed and why. A single strict boundary is cleaner than distributed lenient handling.

**Mock data with planted failures makes features testable.** The Amazon $420 anomaly and the Starbucks duplicates are not random — they are crafted to be detectable by the exact rules the module implements. Writing mock data that exercises the specific code paths being tested is a form of executable documentation: the mock data is a specification of what the anomaly detection and duplicate detection should find.

---

*Constitution v2.0 checklist: This document satisfies Article 5 (trade-off documentation) for App 13.*
