"""Pure decision rules used by the loader.

Deliberately free of I/O and of Kafka/psycopg imports so the behaviour that
matters — lateness, in-batch consolidation, error classification — is unit
testable without a broker or a database.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Error classes recorded on dead letters; they drive how an operator reacts.
DLQ_DESERIALIZATION = "deserialization"
DLQ_VALIDATION = "validation"
DLQ_CONSTRAINT = "warehouse_constraint"
DLQ_UNKNOWN = "unknown"


def parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO-8601 string / datetime into a timezone-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def lateness_seconds(event_time: object, now: datetime | None = None) -> float | None:
    """Seconds between ``event_time`` and ``now`` (negative = in the future)."""
    parsed = parse_timestamp(event_time)
    if parsed is None:
        return None
    reference = now or datetime.now(timezone.utc)
    return (reference - parsed).total_seconds()


def is_late(event_time: object, max_lateness_seconds: int, now: datetime | None = None) -> bool:
    """True when the event is older than the allowed lateness window."""
    seconds = lateness_seconds(event_time, now)
    return seconds is not None and seconds > max_lateness_seconds


def latest_per_key(
    rows: list[dict], key: str = "order_id", timestamp: str = "event_time"
) -> list[dict]:
    """Collapse repeated keys inside a batch, keeping the newest event.

    Consolidating before the upsert means one round-trip per key per batch
    instead of one per record; the warehouse guard still protects against older
    events arriving in a *later* batch.
    """
    newest: dict[object, dict] = {}
    for row in rows:
        existing = newest.get(row.get(key))
        if existing is None:
            newest[row.get(key)] = row
            continue
        if (parse_timestamp(row.get(timestamp)) or datetime.min.replace(tzinfo=timezone.utc)) >= (
            parse_timestamp(existing.get(timestamp)) or datetime.min.replace(tzinfo=timezone.utc)
        ):
            newest[row.get(key)] = row
    return [newest[k] for k in sorted(newest, key=str)]


def headers_to_dict(headers: list[tuple[str, bytes]] | None) -> dict[str, str]:
    """Kafka headers -> plain dict (last value wins, missing values become '')."""
    result: dict[str, str] = {}
    for key, value in headers or []:
        if value is None:
            result[key] = ""
        else:
            result[key] = value.decode("utf-8", errors="replace")
    return result


def dlq_headers(
    original: dict[str, str], error_class: str, error_message: str
) -> list[tuple[str, bytes]]:
    """Headers that make a dead letter actionable without opening the payload."""
    enriched = dict(original)
    enriched["x-error-class"] = error_class
    enriched["x-error-message"] = error_message[:500]
    enriched["x-failed-at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return [(key, value.encode("utf-8")) for key, value in enriched.items()]


def classify_exception(exc: BaseException) -> str:
    """Map an exception to one of the DLQ error classes."""
    name = type(exc).__name__.lower()
    if "json" in name or "decode" in name or "unicode" in name:
        return DLQ_DESERIALIZATION
    if "validation" in name or "schema" in name:
        return DLQ_VALIDATION
    if "integrity" in name or "database" in name or "constraint" in name:
        return DLQ_CONSTRAINT
    return DLQ_UNKNOWN
