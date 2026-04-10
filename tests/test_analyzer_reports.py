"""Integration-style tests for analysis reports and CSV loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from csv_load import load_categorized_file
from metrics import detect_anomalies, run_all_reports
from mock_data import generate_mock_transactions
from output import print_full_analysis


def test_run_all_reports_on_mock() -> None:
    records = generate_mock_transactions()[:20]
    report = run_all_reports(records, payday_date=15)
    assert report["record_count"] == 20
    assert report["top_by_frequency"]
    assert report["anomaly_report"]["anomalies"] is not None


def test_print_full_analysis_runs(capsys: pytest.CaptureFixture[str]) -> None:
    records = generate_mock_transactions()[:5]
    report = run_all_reports(records)
    print_full_analysis(report, duplicate_count=2)
    out = capsys.readouterr().out
    assert "Duplicate transactions skipped" in out


def test_load_categorized_file_minimal_csv(tmp_path: Path) -> None:
    p = tmp_path / "t.csv"
    p.write_text(
        "date,merchant,amount,category,subcategory\n"
        "2024-01-01,Store,10.00,Food,Groceries\n",
        encoding="utf-8",
    )
    records, warnings, dups = load_categorized_file(p)
    assert not warnings
    assert len(records) == 1
    assert not dups


def test_detect_anomalies_flags_high_spend() -> None:
    base = {
        "date": "2024-01-01",
        "category": "X",
        "subcategory": "X",
    }
    records = [
        {**base, "merchant": "Norm1", "amount": 10.0},
        {**base, "merchant": "Norm2", "amount": 10.0},
        {**base, "merchant": "Norm3", "amount": 10.0},
        {**base, "merchant": "Spike", "amount": 100.0},
    ]
    rep = detect_anomalies(records)
    assert any(a["merchant"] == "Spike" for a in rep["anomalies"])


def test_run_all_reports_rejects_bad_record() -> None:
    bad = [{"merchant": "x"}]  # missing date/amount
    with pytest.raises(ValueError, match="Invalid record"):
        run_all_reports(bad)
