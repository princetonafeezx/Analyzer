"""Tests for :mod:`config`."""

from __future__ import annotations

from pathlib import Path

import pytest

from config import AppConfig, load_merged_config


def test_load_merged_config_explicit_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nope.toml"
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_merged_config(explicit=missing)


def test_load_merged_config_invalid_payday(tmp_path: Path) -> None:
    p = tmp_path / "bad.toml"
    p.write_text("payday = 99\n", encoding="utf-8")
    with pytest.raises(ValueError, match="payday must be between"):
        load_merged_config(explicit=p)


def test_load_merged_config_env_overlay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "analyzer.toml").write_text("payday = 10\n", encoding="utf-8")
    override = tmp_path / "extra.toml"
    override.write_text("payday = 20\n", encoding="utf-8")
    monkeypatch.setenv("LL_ANALYZER_CONFIG", str(override))
    cfg = load_merged_config(explicit=None)
    assert cfg.payday == 20


def test_app_config_defaults() -> None:
    assert AppConfig().payday == 15
    assert AppConfig().default_csv is None
