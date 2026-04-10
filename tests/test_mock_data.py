"""Tests for :mod:`mock_data`."""

from __future__ import annotations

from datetime import date

from mock_data import generate_mock_transactions, month_start_from_offset, rule_payload_from_merchant


def test_month_start_from_offset_zero_matches_today() -> None:
    y, m = month_start_from_offset(0)
    t = date.today()
    assert y == t.year and m == t.month


def test_month_start_from_offset_valid_month() -> None:
    y, m = month_start_from_offset(6)
    assert 1 <= m <= 12
    assert y >= 2000


def test_rule_payload_from_merchant_starbucks() -> None:
    p = rule_payload_from_merchant("Starbucks #1")
    assert p["category"] == "Food & Drink"


def test_rule_payload_from_merchant_unknown() -> None:
    p = rule_payload_from_merchant("ZZZ_UNKNOWN_MERCHANT_XYZ")
    assert p["category"] == "Unknown"


def test_generate_mock_transactions_shape() -> None:
    rows = generate_mock_transactions()
    assert len(rows) > 10
    for r in rows[:5]:
        assert "date" in r and "merchant" in r and "amount" in r
        assert "category" in r
