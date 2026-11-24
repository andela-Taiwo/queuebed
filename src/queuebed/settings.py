"""Settings from environment variables, validated once at startup.

Every problem is reported at once, and no error message or log line ever contains the
database password.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit

from queuebed.durations import parse_duration

PREFIX = "QUEUEBED_"


class SettingsError(ValueError):
    """One or more settings are missing or invalid."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("invalid settings:\n" + "\n".join(f"  - {p}" for p in problems))


@dataclass(frozen=True)
class Settings:
    database_url: str
    workers: int
    lease: timedelta
    poll_interval: timedelta
    shutdown_grace: timedelta

    def __repr__(self) -> str:
        return (
            f"Settings(database_url={redact_url(self.database_url)!r}, workers={self.workers}, "
            f"lease={self.lease!r}, poll_interval={self.poll_interval!r}, "
            f"shutdown_grace={self.shutdown_grace!r})"
        )


def redact_url(url: str) -> str:
    """Replace the password in a connection URL with ``***``."""
    parts = urlsplit(url)
    if parts.password is None:
        return url
    host = parts.hostname or ""
    if parts.port is not None:
        host = f"{host}:{parts.port}"
    netloc = f"{parts.username or ''}:***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


_DEFAULTS = {
    "WORKERS": "4",
    "LEASE": "5m",
    "POLL_INTERVAL": "1s",
    "SHUTDOWN_GRACE": "30s",
}


def load_settings(env: Mapping[str, str]) -> Settings:
    """Read settings from ``env`` (normally ``os.environ``), reporting every problem at once."""
    problems: list[str] = []

    def get(name: str) -> str:
        return env.get(PREFIX + name, _DEFAULTS.get(name, "")).strip()

    url = get("DATABASE_URL")
    if not url:
        problems.append(f"{PREFIX}DATABASE_URL is required")
    elif urlsplit(url).scheme not in ("postgresql", "postgres"):
        problems.append(f"{PREFIX}DATABASE_URL must be a postgresql:// URL")

    workers = 0
    raw_workers = get("WORKERS")
    if not raw_workers.isdigit() or not 1 <= int(raw_workers) <= 256:
        problems.append(f"{PREFIX}WORKERS must be a whole number from 1 to 256")
    else:
        workers = int(raw_workers)

    durations: dict[str, timedelta] = {}
    for name in ("LEASE", "POLL_INTERVAL", "SHUTDOWN_GRACE"):
        try:
            durations[name] = parse_duration(get(name))
        except ValueError as exc:
            problems.append(f"{PREFIX}{name}: {exc}")
            continue
        if durations[name] <= timedelta(0):
            problems.append(f"{PREFIX}{name} must be longer than zero")

    if not problems and durations["POLL_INTERVAL"] >= durations["LEASE"]:
        problems.append(f"{PREFIX}POLL_INTERVAL must be shorter than {PREFIX}LEASE")

    if problems:
        raise SettingsError(problems)
    return Settings(
        database_url=url,
        workers=workers,
        lease=durations["LEASE"],
        poll_interval=durations["POLL_INTERVAL"],
        shutdown_grace=durations["SHUTDOWN_GRACE"],
    )
