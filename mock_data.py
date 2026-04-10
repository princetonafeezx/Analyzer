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

def rule_payload_from_merchant(merchant: str) -> CategoryRule:
    normalized = clean_text(merchant)
    for key, payload in DEFAULT_RULES.items():
        rule = clean_text(key)
        if rule in normalized or normalized in rule:
            return payload
    return cast(CategoryRule, {"category": "Unknown", "subcategory": "Unknown"})


