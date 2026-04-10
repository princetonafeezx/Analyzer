"""Tests for :mod:`output` print helpers."""

from __future__ import annotations

from datetime import date

import pytest

from metrics import detect_anomalies
from output import (
    print_anomalies,
    print_day_breakdown,
    print_monthly_trends,
    print_top_frequency,
    print_top_spend,
)


def test_print_top_frequency(capsys: pytest.CaptureFixture[str]) -> None:
    print_top_frequency([{"merchant": "X", "count": 3}])
    out = capsys.readouterr().out
    assert "Top merchants by frequency" in out
    assert "X" in out


def test_print_top_spend(capsys: pytest.CaptureFixture[str]) -> None:
    print_top_spend([{"merchant": "Y", "total": 12.34}])
    out = capsys.readouterr().out
    assert "Top merchants by spend" in out


def test_print_day_breakdown(capsys: pytest.CaptureFixture[str]) -> None:
    print_day_breakdown(
        [{"day": "Monday", "count": 1, "total": 1.0, "average": 1.0}]
    )
    assert "Monday" in capsys.readouterr().out


def test_print_monthly_trends(capsys: pytest.CaptureFixture[str]) -> None:
    print_monthly_trends([{"month": "2024-01", "total": 10.0, "trend": "flat"}])
    assert "2024-01" in capsys.readouterr().out


def test_print_anomalies_empty(capsys: pytest.CaptureFixture[str]) -> None:
    print_anomalies({"anomalies": [], "counts": {}, "affected_categories": set()})
    assert "No anomalies" in capsys.readouterr().out


def test_print_anomalies_non_empty(capsys: pytest.CaptureFixture[str]) -> None:
    base = {"date": date(2024, 1, 1), "category": "K", "subcategory": "K"}
    rep = detect_anomalies(
        [
            {**base, "merchant": "a", "amount": 10.0},
            {**base, "merchant": "b", "amount": 10.0},
            {**base, "merchant": "c", "amount": 10.0},
            {**base, "merchant": "spike", "amount": 100.0},
        ]
    )
    assert rep["anomalies"]
    print_anomalies(rep)
    assert "Anomalies" in capsys.readouterr().out
