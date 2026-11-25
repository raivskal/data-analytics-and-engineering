from datetime import datetime, timedelta, timezone

from src.loader.rules import (
    dlq_headers,
    headers_to_dict,
    is_late,
    lateness_seconds,
    parse_timestamp,
)


def test_parses_iso_with_z_suffix() -> None:
    parsed = parse_timestamp("2024-05-01T10:30:00.000Z")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.hour == 10


def test_parses_offset_and_naive_values() -> None:
    assert parse_timestamp("2024-05-01T10:30:00+02:00").hour == 10
    assert parse_timestamp("2024-05-01 10:30:00").tzinfo is not None


def test_returns_none_for_garbage() -> None:
    assert parse_timestamp("not-a-date") is None
    assert parse_timestamp(None) is None


def test_lateness_boundary_is_inclusive_of_the_window() -> None:
    now = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)
    exactly_one_hour = now - timedelta(hours=1)
    assert is_late(exactly_one_hour, 3600, now) is False
    assert is_late(exactly_one_hour - timedelta(seconds=1), 3600, now) is True


def test_future_events_are_not_late() -> None:
    now = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)
    future = now + timedelta(minutes=5)
    assert lateness_seconds(future, now) == -300
    assert is_late(future, 3600, now) is False


def test_headers_round_trip() -> None:
    headers = [("trace-id", b"abc123"), ("source", b"crm"), ("empty", None)]
    assert headers_to_dict(headers) == {"trace-id": "abc123", "source": "crm", "empty": ""}
    assert headers_to_dict(None) == {}


def test_dead_letter_headers_carry_the_diagnosis() -> None:
    enriched = dict(dlq_headers({"trace-id": "abc123"}, "validation", "status: not allowed"))
    assert enriched["x-error-class"] == b"validation"
    assert b"not allowed" in enriched["x-error-message"]
    assert parse_timestamp(enriched["x-failed-at"].decode()) is not None
    assert enriched["trace-id"] == b"abc123"
