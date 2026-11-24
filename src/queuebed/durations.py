"""Human-readable durations such as ``250ms``, ``30s`` and ``1h30m``.

Job timeouts, lease lengths, retry delays and schedules are all configured as durations. One
parser means one set of rules and one set of error messages.
"""

from __future__ import annotations

import re
from datetime import timedelta

_UNITS_MS = {"ms": 1, "s": 1000, "m": 60_000, "h": 3_600_000, "d": 86_400_000}
_ORDER = ["d", "h", "m", "s", "ms"]
_PART = re.compile(r"(\d+)(ms|s|m|h|d)")


def parse_duration(text: str) -> timedelta:
    """Parse a duration like ``90s``, ``1h30m`` or ``2d``.

    Units are d, h, m, s and ms, each used at most once, largest first. A bare ``0`` is
    allowed; any other number needs a unit.
    """
    value = text.strip()
    if value == "0":
        return timedelta(0)
    if not value:
        raise ValueError("duration is empty")
    pos = 0
    total_ms = 0
    last_rank = -1
    for match in _PART.finditer(value):
        if match.start() != pos:
            break
        unit = match.group(2)
        rank = _ORDER.index(unit)
        if rank <= last_rank:
            raise ValueError(f"duration {text!r}: units must be in order d, h, m, s, ms, once each")
        last_rank = rank
        total_ms += int(match.group(1)) * _UNITS_MS[unit]
        pos = match.end()
    if pos != len(value):
        raise ValueError(f"duration {text!r} is not valid; use forms like 250ms, 30s or 1h30m")
    return timedelta(milliseconds=total_ms)


def format_duration(duration: timedelta) -> str:
    """Format a duration in the same form ``parse_duration`` reads."""
    if duration < timedelta(0):
        raise ValueError("duration cannot be negative")
    remaining = duration // timedelta(milliseconds=1)
    if remaining == 0:
        return "0"
    parts = []
    for unit in _ORDER:
        size = _UNITS_MS[unit]
        count, remaining = divmod(remaining, size)
        if count:
            parts.append(f"{count}{unit}")
    return "".join(parts)
