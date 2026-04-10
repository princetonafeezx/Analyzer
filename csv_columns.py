
from __future__ import annotations

import re
from collections.abc import Callable

from textutil import clean_text


def _header_tokens(norm: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", norm))

def _score_date(norm: str, tokens: set[str]) -> float:
    for phrase in (
        "transaction date",
        "posting date",
        "posted date",
        "post date",
        "trans date",
        "value date",
        "book date",
    ):
        if phrase in norm:
            return 14.0
    if norm in {"date", "dt"}:
        return 13.0
    if "date" in tokens:
        return 9.0
    return 0.0
