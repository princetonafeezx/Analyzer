"""Tests for :mod:`categorizer` interactive menu."""

from __future__ import annotations

import categorizer


def test_categorizer_menu_quit(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _p="": "5")
    categorizer.menu()
