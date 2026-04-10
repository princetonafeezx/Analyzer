"""Tests for :mod:`textutil`."""

from __future__ import annotations

from textutil import clean_text, similarity_ratio


def test_clean_text_normalizes() -> None:
    assert clean_text("  Foo & Bar / Baz  ") == "foo bar baz"


def test_similarity_identical() -> None:
    assert similarity_ratio("starbucks", "starbucks") == 1.0


def test_similarity_both_empty_cleaned() -> None:
    assert similarity_ratio("   ", "...") == 1.0


def test_similarity_one_empty() -> None:
    assert similarity_ratio("a", "") == 0.0


def test_similarity_substring_shortcut() -> None:
    score = similarity_ratio("sbux", "starbucks sbux downtown")
    assert 0 < score <= 1.0


def test_similarity_levenshtein_path() -> None:
    """Distinct strings with no substring relation exercise edit-distance scoring."""
    a, b = "kitten", "sitting"
    s = similarity_ratio(a, b)
    assert 0.0 < s < 1.0
