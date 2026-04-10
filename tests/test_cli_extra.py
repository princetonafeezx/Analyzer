"""Extra tests for :mod:`cli`."""

from __future__ import annotations

from pathlib import Path

import pytest

import cli


def test_cli_invalid_payday_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--payday", "99", "version"]) == 1
    assert "error:" in capsys.readouterr().err


def test_cli_config_file_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    missing = tmp_path / "nope.toml"
    assert cli.main(["--config", str(missing), "version"]) == 1


def test_cli_menu_subcommand_calls_menu(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[int] = []

    def capture(*, initial_payday: int = 15) -> None:
        seen.append(initial_payday)

    monkeypatch.setattr("menu.menu", capture)
    assert cli.main(["--payday", "12", "menu"]) == 0
    assert seen == [12]


def test_entrypoint_propagates_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "main", lambda argv=None: 3)
    with pytest.raises(SystemExit) as exc:
        cli.entrypoint()
    assert exc.value.code == 3
