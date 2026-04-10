"""Tests for additional :mod:`categorizer` APIs."""

from __future__ import annotations

from pathlib import Path

import pytest

import categorizer
from schemas import CategoryRule


def test_categorizer_detect_columns_delegates() -> None:
    headers = ["Date", "Merchant", "Amount"]
    m = categorizer.detect_columns(headers)
    assert m["date"] == 0


def test_read_transaction_file_minimal(tmp_path: Path) -> None:
    p = tmp_path / "t.csv"
    p.write_text("Date,Merchant,Amount\n2024-01-01,Store,12.34\n", encoding="utf-8")
    rows, warnings = categorizer.read_transaction_file(p)
    assert not warnings
    assert len(rows) == 1
    assert rows[0]["merchant"] == "Store"
    assert rows[0]["amount"] == 12.34


def test_read_transaction_file_empty(tmp_path: Path) -> None:
    p = tmp_path / "e.csv"
    p.write_text("", encoding="utf-8")
    rows, warnings = categorizer.read_transaction_file(p)
    assert rows == []
    assert warnings


def test_read_transaction_file_missing() -> None:
    with pytest.raises(FileNotFoundError):
        categorizer.read_transaction_file("/nonexistent/path/file.csv")


def test_categorizer_generate_mock_transactions() -> None:
    rows = categorizer.generate_mock_transactions()
    assert len(rows) >= 10
    assert "date" in rows[0]


def test_categorize_transactions() -> None:
    rules: dict[str, CategoryRule] = {
        "starbucks": {"category": "Food & Drink", "subcategory": "Coffee"},
    }
    txs = [{"date": "2024-01-01", "merchant": "STARBUCKS 1", "amount": 5.0}]
    cat, flagged = categorizer.categorize_transactions(txs, rules)
    assert len(cat) == 1
    assert cat[0]["category"] == "Food & Drink"


def test_run_classification_mock() -> None:
    result = categorizer.run_classification(use_mock=True)
    assert result["records"]
    assert "summary" in result


def test_run_classification_from_csv(tmp_path: Path) -> None:
    p = tmp_path / "in.csv"
    p.write_text("Date,Merchant,Amount\n2024-01-01,Store,5.00\n", encoding="utf-8")
    result = categorizer.run_classification(file_path=p, use_mock=False)
    assert result["records"]
    assert result["rules"]


def test_run_classification_requires_path() -> None:
    with pytest.raises(ValueError, match="file path"):
        categorizer.run_classification(use_mock=False, file_path=None)


def test_print_rules(capsys: pytest.CaptureFixture[str]) -> None:
    categorizer.print_rules({"foo": {"category": "Food & Drink", "subcategory": "X"}})
    out = capsys.readouterr().out
    assert "foo" in out or "Food" in out


def test_print_summary_with_flagged(capsys: pytest.CaptureFixture[str]) -> None:
    rec = {
        "date": "2024-01-01",
        "merchant": "m",
        "amount": 1.0,
        "category": "Unknown",
        "subcategory": "Unknown",
        "confidence": 0.1,
        "match_type": "unknown",
    }
    categorizer.print_summary([rec], [rec])
    out = capsys.readouterr().out
    assert "Unknown" in out


def test_add_rule_interactively_success(monkeypatch: pytest.MonkeyPatch) -> None:
    rules: dict[str, CategoryRule] = {}
    answers = iter(["mymerchant", "Food & Drink", "Coffee"])
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    categorizer.add_rule_interactively(rules)
    assert "mymerchant" in rules or any("mymerchant" in k for k in rules)


def test_add_rule_interactively_blank_merchant(monkeypatch: pytest.MonkeyPatch) -> None:
    rules: dict[str, CategoryRule] = {}
    monkeypatch.setattr("builtins.input", lambda _p="": "")
    categorizer.add_rule_interactively(rules)
    assert rules == {}
