"""Tests for :mod:`version`."""

from __future__ import annotations

from version import __version__


def test_version_string() -> None:
    assert isinstance(__version__, str)
    assert __version__
    assert __version__[0].isdigit()
