"""Tests for :mod:`storage`."""

from __future__ import annotations

from pathlib import Path

import storage


def test_get_data_dir_explicit(tmp_path: Path) -> None:
    d = storage.get_data_dir(tmp_path / "data")
    assert d.is_dir()
    assert d == tmp_path / "data"


def test_get_data_dir_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANALYZER_DATA_DIR", str(tmp_path / "from_env"))
    d = storage.get_data_dir()
    assert d == tmp_path / "from_env"
    assert d.is_dir()


def test_format_money() -> None:
    assert storage.format_money(1234.5) == "$1,234.50"


def test_save_and_load_categorized_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "out.csv"
    records = [
        {
            "date": "2024-01-01",
            "merchant": "M",
            "amount": 10.0,
            "category": "Food",
            "subcategory": "Food",
            "confidence": 1.0,
            "match_type": "exact",
        }
    ]
    storage.save_categorized_transactions(records, path)
    loaded, warnings = storage.load_categorized_transactions(path)
    assert not warnings
    assert len(loaded) == 1
    assert loaded[0]["merchant"] == "M"
    assert loaded[0]["amount"] == 10.0
