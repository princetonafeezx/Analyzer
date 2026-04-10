"""Tests for :mod:`records`."""

from __future__ import annotations

from datetime import date

import pytest

from records import coerce_analysis_records, normalize_analysis_record


def test_normalize_analysis_record_from_strings() -> None:
    rec = normalize_analysis_record(
        {
            "date": "2024-06-15",
            "merchant": "  X  ",
            "amount": "12.50",
            "category": "Food",
            "subcategory": "Lunch",
        }
    )
    assert rec["date"] == date(2024, 6, 15)
    assert rec["merchant"] == "X"
    assert rec["amount"] == 12.5
    assert rec["category"] == "Food"
    assert rec["subcategory"] == "Lunch"


def test_normalize_analysis_record_bool_amount_rejected() -> None:
    with pytest.raises(ValueError, match="invalid amount type"):
        normalize_analysis_record(
            {
                "date": "2024-01-01",
                "merchant": "m",
                "amount": True,
                "category": "X",
            }
        )


def test_normalize_missing_date() -> None:
    with pytest.raises(ValueError, match="missing required field 'date'"):
        normalize_analysis_record({"merchant": "m", "amount": 1.0, "category": "X"})


def test_coerce_analysis_records_success() -> None:
    rows = [
        {
            "date": "2024-01-01",
            "merchant": "a",
            "amount": 1.0,
            "category": "C",
        }
    ]
    out = coerce_analysis_records(rows)
    assert len(out) == 1


def test_coerce_analysis_records_index_error() -> None:
    with pytest.raises(ValueError, match="Invalid record at index 1"):
        coerce_analysis_records(
            [
                {
                    "date": "2024-01-01",
                    "merchant": "a",
                    "amount": 1.0,
                    "category": "C",
                },
                {"merchant": "bad"},
            ]
        )
