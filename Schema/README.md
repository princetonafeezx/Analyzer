# Schema folder for `Analyzer`

This folder contains simple **JSON Schema** files derived from the repository's current public data shapes.

Included focus areas:
- categorized transaction rows
- classification output
- analysis/report output
- reconciliation output
- duplicate detection output
- basic `analyzer.toml` config

## Suggested placement

Copy this folder into the repository root as:

```text
Analyzer/
└── Schema/
```

## Notes

- These schemas are intentionally simple and are meant for documentation, validation, and API/export contracts.
- They are based on the repository's existing `schemas.py`, plus the config keys documented in `README.md`.
- JSON Schema date fields use `format: "date"` and expect ISO-style values such as `2026-04-10`.
- `output_path` is represented as a string or null for portability.

## Main files

- `categorized-record.schema.json`
- `classification-result.schema.json`
- `analysis-report.schema.json`
- `reconciliation-report.schema.json`
- `duplicate-detection-result.schema.json`
- `run-reconciliation-result.schema.json`
- `analyzer-config.schema.json`
- `schema-index.json`
