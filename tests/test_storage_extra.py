"""Extra tests for :mod:`storage` path helpers and JSON/text I/O."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import storage


def test_path_helpers_under_base(tmp_path: Path) -> None:
    base = tmp_path / "d"
    assert storage.get_categorized_path(base) == base / "categorized_transactions.csv"
    assert storage.get_report_path(base) == base / "analyzer_report.txt"
    assert storage.get_budget_profile_path(base) == base / "budget_profile.json"
    assert storage.get_investment_profile_path(base) == base / "investment_scenarios.json"


def test_save_and_load_json_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "x.json"
    data = {"a": 1, "b": [2, 3]}
    storage.save_json(data, p)
    assert json.loads(p.read_text(encoding="utf-8")) == data
    assert storage.load_json(p) == data


def test_load_json_missing_uses_default(tmp_path: Path) -> None:
    p = tmp_path / "missing.json"
    assert storage.load_json(p, default={"k": 1}) == {"k": 1}


def test_load_json_invalid_warns(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{", encoding="utf-8")
    with pytest.warns(UserWarning):
        out = storage.load_json(p, default={"fallback": True})
    assert out == {"fallback": True}


def test_write_text_report(tmp_path: Path) -> None:
    path = storage.write_text_report("hello", tmp_path / "r.txt")
    assert path.read_text(encoding="utf-8") == "hello"


def test_load_categorized_warns_bad_amount(tmp_path: Path) -> None:
    p = tmp_path / "c.csv"
    p.write_text(
        "date,merchant,amount,category,subcategory,confidence,match_type\n"
        "2024-01-01,M,notmoney,Food,Food,1,exact\n",
        encoding="utf-8",
    )
    rows, warnings = storage.load_categorized_transactions(p)
    assert len(rows) == 1
    assert rows[0]["amount"] == 0.0
    assert warnings
