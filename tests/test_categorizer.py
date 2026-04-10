"""Tests for :mod:`categorizer`."""

from __future__ import annotations

import categorizer
from schemas import CategoryRule


def test_find_best_rule_match_exact_substring() -> None:
    rules: dict[str, CategoryRule] = {
        "starbucks": {"category": "Food & Drink", "subcategory": "Coffee"},
    }
    m = categorizer.find_best_rule_match("STARBUCKS #1023", rules)
    assert m["category"] == "Food & Drink"
    assert m["match_type"] == "exact"
    assert m["confidence"] == 1.0


def test_find_best_rule_match_unknown() -> None:
    rules: dict[str, CategoryRule] = {"zzz": {"category": "Shopping", "subcategory": "Misc"}}
    m = categorizer.find_best_rule_match("qqqqqqqq", rules, threshold=0.99)
    assert m["category"] == "Unknown"
    assert m["match_type"] == "unknown"


def test_summarize_categories() -> None:
    rows = [
        {"category": "A", "amount": 10.0},
        {"category": "A", "amount": 5.0},
        {"category": "B", "amount": 3.0},
    ]
    summary = categorizer.summarize_categories(rows)
    by_cat = {r["category"]: r for r in summary}
    assert by_cat["A"]["count"] == 2
    assert by_cat["A"]["total"] == 15.0
    assert by_cat["B"]["total"] == 3.0
