from __future__ import annotations

import re

_SAFE_PART = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


def safe_id(value: str, kind: str = "id") -> str:
    """Validate a value is safe to use as a single path component.

    Rejects separators and traversal sequences so attacker-supplied ids can
    never escape the intended data directory.
    """
    if not isinstance(value, str) or not _SAFE_PART.match(value):
        raise ValueError(f"invalid {kind}")
    if value in (".", ".."):
        raise ValueError(f"invalid {kind}")
    return value
