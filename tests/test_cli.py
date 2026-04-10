"""Tests for the ``ll-analyzer`` CLI and config loading."""

from __future__ import annotations

import pytest

from cli import main
from config import load_merged_config


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["version"]) == 0
    out = capsys.readouterr().out.strip()
    assert out
    assert out[0].isdigit()


def test_cli_analyze_mock(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["analyze", "--mock"]) == 0
    out = capsys.readouterr().out
    assert "Top merchants by frequency" in out


def test_cli_analyze_missing_source(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["analyze"]) == 2
    err = capsys.readouterr().err
    assert "error:" in err


def test_cli_default_menu_invokes_helpable_parser() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_config_payday_from_cwd_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "analyzer.toml").write_text("payday = 22\n", encoding="utf-8")
    cfg = load_merged_config(explicit=None)
    assert cfg.payday == 22


def test_config_explicit_file(tmp_path) -> None:
    p = tmp_path / "x.toml"
    p.write_text('payday = 7\ndefault_csv = ""\n', encoding="utf-8")
    cfg = load_merged_config(explicit=p)
    assert cfg.payday == 7
