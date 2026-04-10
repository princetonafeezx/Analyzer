"""Tests for :mod:`parsing`."""

from __future__ import annotations

from datetime import date

import pytest

from parsing import parse_amount, parse_date


def test_parse_date_iso_and_us_slash() -> None:
    assert parse_date("2024-01-15") == date(2024, 1, 15)
    assert parse_date("01/15/2024") == date(2024, 1, 15)


def test_parse_date_ambiguous_month_first() -> None:
    assert parse_date("01/02/2024") == date(2024, 1, 2)


def test_parse_date_day_month_when_day_gt_12() -> None:
    assert parse_date("31/01/2024") == date(2024, 1, 31)


def test_parse_date_invalid() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        parse_date("not-a-date")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("12.34", 12.34),
        ("$1,234.56", 1234.56),
        ("(10.00)", 10.0),
        ("-5.00", 5.0),
    ],
)
def test_parse_amount_common(text: str, expected: float) -> None:
    assert parse_amount(text) == expected


def test_parse_amount_rejects_scientific() -> None:
    with pytest.raises(ValueError, match="Scientific notation"):
        parse_amount("1e2")


def test_parse_amount_blank() -> None:
    with pytest.raises(ValueError, match="Blank"):
        parse_amount("   ")
