from __future__ import annotations

from datetime import date
from typing import cast

from categorizer import DEFAULT_RULES
from schemas import CategorizedRecord, CategoryRule
from textutil import clean_text


def month_start_from_offset(offset: int) -> tuple[int, int]:
    today = date.today()
    month = today.month - offset
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return year, month



