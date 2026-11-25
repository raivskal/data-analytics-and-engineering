"""Idempotent, transactional writes into the PostgreSQL warehouse.

Two invariants make replays safe:

1. ``raw.events`` has ``UNIQUE (topic, partition_id, kafka_offset)`` — the same
   Kafka record can be consumed twice without duplicating rows.
2. ``landing.*`` upserts only when ``EXCLUDED.updated_at >= target.updated_at``
   — a replayed or out-of-order event can never roll an entity back in time.

Everything for one poll batch happens inside a single transaction, and the
consumer commits its offsets only after that transaction returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import psycopg
from psycopg.types.json import Json

INSERT_RAW_EVENT = """
INSERT INTO raw.events
    (topic, partition_id, kafka_offset, message_key, event_id, event_time, headers, payload)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ON CONSTRAINT raw_events_unique_offset DO NOTHING
"""

UPSERT_ORDER = """
INSERT INTO landing.orders AS target
    (order_id, customer_id, store_id, status, currency, order_amount, item_count,
     event_id, event_time, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (order_id) DO UPDATE SET
    customer_id  = EXCLUDED.customer_id,
    store_id     = EXCLUDED.store_id,
    status       = EXCLUDED.status,
    currency     = EXCLUDED.currency,
    order_amount = EXCLUDED.order_amount,
    item_count   = EXCLUDED.item_count,
    event_id     = EXCLUDED.event_id,
    event_time   = EXCLUDED.event_time,
    updated_at   = EXCLUDED.updated_at,
    ingested_at  = now()
WHERE EXCLUDED.updated_at >= target.updated_at
"""

UPSERT_PAYMENT = """
INSERT INTO landing.payments AS target
    (payment_id, order_id, method, amount, status, event_id, event_time, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (payment_id) DO UPDATE SET
    order_id   = EXCLUDED.order_id,
    method     = EXCLUDED.method,
    amount     = EXCLUDED.amount,
    status     = EXCLUDED.status,
    event_id   = EXCLUDED.event_id,
    event_time = EXCLUDED.event_time,
    updated_at = EXCLUDED.updated_at
WHERE EXCLUDED.updated_at >= target.updated_at
"""

UPSERT_CUSTOMER = """
INSERT INTO landing.customers AS target
    (customer_id, email, full_name, country, segment, is_deleted, event_id, event_time, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (customer_id) DO UPDATE SET
    email      = EXCLUDED.email,
    full_name  = EXCLUDED.full_name,
    country    = EXCLUDED.country,
    segment    = EXCLUDED.segment,
    is_deleted = EXCLUDED.is_deleted,
    event_id   = EXCLUDED.event_id,
    event_time = EXCLUDED.event_time,
    updated_at = EXCLUDED.updated_at
WHERE EXCLUDED.updated_at >= target.updated_at
"""

INSERT_DLQ = """
INSERT INTO raw.dlq
    (topic, partition_id, kafka_offset, message_key, error_class, error_message, headers, payload)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ON CONSTRAINT raw_dlq_unique_offset DO NOTHING
"""

INSERT_LATE = """
INSERT INTO raw.late_events
    (topic, partition_id, kafka_offset, event_id, event_time, lateness_seconds, payload)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ON CONSTRAINT raw_late_events_unique_offset DO NOTHING
"""

UPSERT_WATERMARK = """
INSERT INTO ops.watermarks AS target
    (topic, max_event_time, max_ingested_at, records_seen, updated_at)
VALUES (%s, %s, %s, %s, now())
ON CONFLICT (topic) DO UPDATE SET
    max_event_time  = GREATEST(target.max_event_time, EXCLUDED.max_event_time),
    max_ingested_at = GREATEST(target.max_ingested_at, EXCLUDED.max_ingested_at),
    records_seen    = target.records_seen + EXCLUDED.records_seen,
    updated_at      = now()
"""

INSERT_METRIC = """
INSERT INTO ops.pipeline_metrics (metric, topic, value, labels) VALUES (%s, %s, %s, %s)
"""


@dataclass
class Batch:
    """Everything one poll cycle wants to persist, in one transaction."""

    raw_events: list[tuple] = field(default_factory=list)
    orders: list[tuple] = field(default_factory=list)
    payments: list[tuple] = field(default_factory=list)
    customers: list[tuple] = field(default_factory=list)
    dead_letters: list[tuple] = field(default_factory=list)
    late_events: list[tuple] = field(default_factory=list)
    watermarks: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class BatchResult:
    raw_inserted: int = 0
    raw_duplicates: int = 0
    orders_upserted: int = 0
    orders_ignored: int = 0
    payments_upserted: int = 0
    customers_upserted: int = 0
    dead_letters: int = 0
    late_events: int = 0

    def as_metrics(self) -> dict[str, float]:
        return {
            "raw_inserted": float(self.raw_inserted),
            "raw_duplicates": float(self.raw_duplicates),
            "orders_upserted": float(self.orders_upserted),
            "orders_ignored_stale": float(self.orders_ignored),
            "payments_upserted": float(self.payments_upserted),
            "customers_upserted": float(self.customers_upserted),
            "dead_letters": float(self.dead_letters),
            "late_events": float(self.late_events),
        }


def order_row(payload: dict, updated_at: datetime) -> tuple:
    return (
        payload["order_id"],
        payload["customer_id"],
        int(payload["store_id"]),
        payload["status"],
        payload["currency"],
        payload["amount"],
        int(payload["item_count"]),
        payload["event_id"],
        payload["event_time"],
        updated_at,
    )


def payment_row(payload: dict, updated_at: datetime) -> tuple:
    return (
        payload["payment_id"],
        payload["order_id"],
        payload["method"],
        payload["amount"],
        payload["status"],
        payload["event_id"],
        payload["event_time"],
        updated_at,
    )


def customer_row(payload: dict, updated_at: datetime) -> tuple:
    return (
        payload["customer_id"],
        payload.get("email"),
        payload.get("full_name"),
        payload.get("country"),
        payload.get("segment"),
        payload.get("op") == "delete",
        payload["event_id"],
        payload["event_time"],
        updated_at,
    )


class Warehouse:
    """Thin, explicit data-access layer; one connection per loader process."""

    def __init__(self, dsn: str) -> None:
        self._conn = psycopg.connect(dsn, autocommit=False, application_name="warehouse-loader")

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Warehouse:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def write_batch(self, batch: Batch) -> BatchResult:
        result = BatchResult()
        with self._conn.transaction(), self._conn.cursor() as cur:
            if batch.raw_events:
                cur.executemany(INSERT_RAW_EVENT, batch.raw_events)
                result.raw_inserted = max(cur.rowcount, 0)
                result.raw_duplicates = len(batch.raw_events) - result.raw_inserted

            if batch.orders:
                cur.executemany(UPSERT_ORDER, batch.orders)
                result.orders_upserted = max(cur.rowcount, 0)
                result.orders_ignored = len(batch.orders) - result.orders_upserted

            if batch.payments:
                cur.executemany(UPSERT_PAYMENT, batch.payments)
                result.payments_upserted = max(cur.rowcount, 0)

            if batch.customers:
                cur.executemany(UPSERT_CUSTOMER, batch.customers)
                result.customers_upserted = max(cur.rowcount, 0)

            if batch.dead_letters:
                cur.executemany(INSERT_DLQ, batch.dead_letters)
                result.dead_letters = max(cur.rowcount, 0)

            if batch.late_events:
                cur.executemany(INSERT_LATE, batch.late_events)
                result.late_events = max(cur.rowcount, 0)

            for topic, marks in batch.watermarks.items():
                cur.execute(
                    UPSERT_WATERMARK,
                    (
                        topic,
                        marks.get("max_event_time"),
                        marks.get("max_ingested_at"),
                        marks.get("records", 0),
                    ),
                )
        return result

    def record_metric(
        self, metric: str, value: float, topic: str | None = None, labels: dict | None = None
    ) -> None:
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute(INSERT_METRIC, (metric, topic, value, Json(labels or {})))

    def health(self) -> dict[str, Any]:
        with self._conn.cursor() as cur:
            cur.execute("SELECT * FROM ops.pipeline_health")
            row = cur.fetchone()
            columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))

