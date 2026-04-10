"""Tests for :mod:`csv_load`."""

from __future__ import annotations

from pathlib import Path

import pytest

from csv_load import load_categorized_file


def test_load_categorized_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_categorized_file(tmp_path / "missing.csv")


def test_load_categorized_file_empty(tmp_path: Path) -> None:
    p = tmp_path / "e.csv"
    p.write_text("", encoding="utf-8")
    recs, warnings, dups = load_categorized_file(p)
    assert recs == []
    assert warnings
    assert dups == []


def test_load_categorized_file_duplicate_key(tmp_path: Path) -> None:
    p = tmp_path / "d.csv"
    body = (
        "date,merchant,amount,category,subcategory\n"
        "2024-01-01,Same,10.00,Food,Food\n"
        "2024-01-01,Same,10.00,Food,Food\n"
    )
    p.write_text(body, encoding="utf-8")
    recs, warnings, dups = load_categorized_file(p)
    assert len(recs) == 1
    assert len(dups) == 1
    assert not warnings


def test_load_categorized_file_skips_bad_row(tmp_path: Path) -> None:
    p = tmp_path / "x.csv"
    p.write_text(
        "date,merchant,amount,category,subcategory\n"
        "2024-01-01,OK,1.00,Food,Food\n"
        "not-a-date,BAD,xx,Food,Food\n",
        encoding="utf-8",
    )
    recs, warnings, dups = load_categorized_file(p)
    assert len(recs) == 1
    assert warnings
    assert not dups
