"""Tests for :mod:`csv_columns`."""

from __future__ import annotations

from csv_columns import detect_columns


def test_detect_columns_standard_headers() -> None:
    headers = ["Date", "Merchant", "Amount", "Category", "Subcategory"]
    m = detect_columns(headers)
    assert m["date"] == 0
    assert m["merchant"] == 1
    assert m["amount"] == 2
    assert m["category"] == 3
    assert m["subcategory"] == 4


def test_detect_columns_flexible_names() -> None:
    headers = ["Transaction Date", "Payee", "Debit", "Cat", "Sub"]
    m = detect_columns(headers)
    assert m["date"] is not None
    assert m["merchant"] is not None
    assert m["amount"] is not None
    assert m["category"] is not None
