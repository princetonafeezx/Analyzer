
from __future__ import annotations

import re
from collections.abc import Callable

from textutil import clean_text


def _header_tokens(norm: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", norm))


