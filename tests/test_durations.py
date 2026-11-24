from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from queuebed.durations import format_duration, parse_duration


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0", timedelta(0)),
        ("250ms", timedelta(milliseconds=250)),
        ("30s", timedelta(seconds=30)),
        ("1h30m", timedelta(hours=1, minutes=30)),
        ("2d", timedelta(days=2)),
        ("1d2h3m4s5ms", timedelta(days=1, hours=2, minutes=3, seconds=4, milliseconds=5)),
        (" 90s ", timedelta(seconds=90)),
    ],
)
def test_parse(text: str, expected: timedelta) -> None:
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    "text", ["", "30", "1.5s", "-5s", "5 s", "30m1h", "1s1s", "1w", "s", "1h 30m", "10sms"]
)
def test_invalid_durations_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        parse_duration(text)


def test_error_names_the_bad_value() -> None:
    with pytest.raises(ValueError, match="'5x'"):
        parse_duration("5x")


@pytest.mark.parametrize(
    ("duration", "text"),
    [
        (timedelta(0), "0"),
        (timedelta(milliseconds=250), "250ms"),
        (timedelta(hours=1, minutes=30), "1h30m"),
        (timedelta(days=3, seconds=1), "3d1s"),
    ],
)
def test_format(duration: timedelta, text: str) -> None:
    assert format_duration(duration) == text


@given(st.integers(0, 10**12))
def test_round_trip(ms: int) -> None:
    duration = timedelta(milliseconds=ms)
    assert parse_duration(format_duration(duration)) == duration


def test_negative_duration_cannot_be_formatted() -> None:
    with pytest.raises(ValueError):
        format_duration(timedelta(seconds=-1))
