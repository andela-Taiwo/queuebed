from datetime import timedelta

import pytest

from queuebed.settings import SettingsError, load_settings, redact_url

URL = "postgresql://app:s3cret-pw@localhost:5432/queuebed"


def test_defaults() -> None:
    settings = load_settings({"QUEUEBED_DATABASE_URL": URL})
    assert settings.workers == 4
    assert settings.lease == timedelta(minutes=5)
    assert settings.poll_interval == timedelta(seconds=1)
    assert settings.shutdown_grace == timedelta(seconds=30)


def test_overrides() -> None:
    settings = load_settings(
        {"QUEUEBED_DATABASE_URL": URL, "QUEUEBED_WORKERS": "16", "QUEUEBED_LEASE": "1h"}
    )
    assert settings.workers == 16
    assert settings.lease == timedelta(hours=1)


def test_every_problem_is_reported_at_once() -> None:
    with pytest.raises(SettingsError) as info:
        load_settings({"QUEUEBED_WORKERS": "0", "QUEUEBED_LEASE": "soon"})
    problems = info.value.problems
    assert len(problems) == 3
    assert any("DATABASE_URL is required" in p for p in problems)
    assert any("WORKERS" in p for p in problems)
    assert any("LEASE" in p for p in problems)


def test_non_postgres_url_is_rejected() -> None:
    with pytest.raises(SettingsError, match="postgresql"):
        load_settings({"QUEUEBED_DATABASE_URL": "mysql://app:pw@db/q"})


def test_poll_interval_must_be_shorter_than_lease() -> None:
    with pytest.raises(SettingsError, match="POLL_INTERVAL"):
        load_settings(
            {"QUEUEBED_DATABASE_URL": URL, "QUEUEBED_LEASE": "5s", "QUEUEBED_POLL_INTERVAL": "5s"}
        )


def test_zero_duration_is_rejected() -> None:
    with pytest.raises(SettingsError, match="SHUTDOWN_GRACE"):
        load_settings({"QUEUEBED_DATABASE_URL": URL, "QUEUEBED_SHUTDOWN_GRACE": "0"})


def test_redact_url() -> None:
    assert redact_url(URL) == "postgresql://app:***@localhost:5432/queuebed"
    assert redact_url("postgresql://localhost/queuebed") == "postgresql://localhost/queuebed"


def test_password_never_appears_in_repr_or_errors() -> None:
    settings = load_settings({"QUEUEBED_DATABASE_URL": URL})
    assert "s3cret-pw" not in repr(settings)
    with pytest.raises(SettingsError) as info:
        load_settings({"QUEUEBED_DATABASE_URL": URL, "QUEUEBED_WORKERS": "x"})
    assert "s3cret-pw" not in str(info.value)
