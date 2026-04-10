"""Tests for :mod:`menu` interactive entry."""

from __future__ import annotations

import menu as menu_mod


def test_menu_quit_immediately(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _p="": "6")
    menu_mod.menu(initial_payday=15)


def test_menu_main_uses_config(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "analyzer.toml").write_text("payday = 18\n", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _p="": "6")
    menu_mod.main()
