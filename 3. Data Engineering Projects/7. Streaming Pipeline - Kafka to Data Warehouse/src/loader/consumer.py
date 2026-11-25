"""Consume events and load them into the warehouse.

Delivery semantics, stated plainly:

* the consumer runs with ``enable.auto.commit=false`` and commits **after** the
  warehouse transaction returns, so a crash re-delivers the batch instead of
  losing it (at-least-once);
* the warehouse writes are idempotent (unique offsets + guarded upserts), so a
  re-delivered batch produces no duplicates — the combination is effectively
  exactly-once as observed in the warehouse;
* records that can never be processed (bad framing, schema violations, unknown
  topics) are dead-lettered and the loop keeps going instead of blocking a
  partition;
* events older than ``MAX_LATENESS_SECONDS`` are quarantined in
  ``raw.late_events`` and reconciled separately rather than silently applied.
"""

from __future__ import annotations

import argparse
import signal
import sys
from dataclasses import dataclass
from datetime import datetime, timezone

from confluent_kafka import Consumer, KafkaError, Message
from psycopg.types.json import Json

from src.common.config import Settings, get_settings
from src.common.logging import configure_logging, get_logger
from src.common.schemas import validation_errors
from src.loader.decoding import PayloadDecodeError, decode_value
from src.loader.dlq import DeadLetterPublisher
from src.loader.rules import (
    DLQ_DESERIALIZATION,
    DLQ_VALIDATION,
    headers_to_dict,
    is_late,
    latest_per_key,
    lateness_seconds,
    parse_timestamp,
)
from src.loader.warehouse import Batch, BatchResult, Warehouse, customer_row, order_row, payment_row

log = get_logger(__name__)


@dataclass
class LoaderStats:
    polls: int = 0
    records: int = 0
    raw_inserted: int = 0
    raw_duplicates: int = 0
    orders: int = 0
    orders_ignored_stale: int = 0
    payments: int = 0
    customers: int = 0
    dead_letters: int = 0
    late_events: int = 0

    def absorb(self, result: BatchResult) -> None:
        self.raw_inserted += result.raw_inserted
        self.raw_duplicates += result.raw_duplicates
        self.orders += result.orders_upserted
        self.orders_ignored_stale += result.orders_ignored
        self.payments += result.payments_upserted
        self.customers += result.customers_upserted
        self.dead_letters += result.dead_letters
        self.late_events += result.late_events


def build_consumer(settings: Settings) -> Consumer:
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka.bootstrap_servers,
            "group.id": settings.loader.group_id,
            "client.id": "warehouse-loader",
            # Durable hand-off: offsets are committed by us, after the DB commit.
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
            "max.poll.interval.ms": 300_000,
            "session.timeout.ms": 30_000,
            "fetch.min.bytes": 1,
            "enable.partition.eof": False,
            # Cooperative rebalancing avoids stop-the-world partition revokes.
            "partition.assignment.strategy": "cooperative-sticky",
        }
    )
    topics = list(settings.kafka.entity_topics().values())
    consumer.subscribe(topics, on_assign=_on_assign, on_revoke=_on_revoke)
    log.info("subscribed to %s as group '%s'", ", ".join(topics), settings.loader.group_id)
    return consumer


def _on_assign(consumer: Consumer, partitions: list) -> None:  # noqa: ANN001
    assigned = ", ".join(f"{p.topic}[{p.partition}]" for p in partitions)
    log.info("partitions assigned: %s", assigned)


def _on_revoke(consumer: Consumer, partitions: list) -> None:  # noqa: ANN001
    log.info("partitions revoked: %s", ", ".join(f"{p.topic}[{p.partition}]" for p in partitions))


class WarehouseLoader:
    """Poll -> validate -> transactional write -> commit offsets."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._consumer = build_consumer(settings)
        self._warehouse = Warehouse(settings.postgres.dsn)
        self._dlq = DeadLetterPublisher(settings.kafka)
        self._stats = LoaderStats()
        self._stopping = False
        signal.signal(signal.SIGINT, self._request_stop)
        signal.signal(signal.SIGTERM, self._request_stop)

    def _request_stop(self, signum: int, _frame: object) -> None:
        log.info("shutdown requested (signal %s); finishing the current batch", signum)
        self._stopping = True

    def _limit_reached(self, max_messages: int | None) -> bool:
        return max_messages is not None and self._stats.records >= max_messages

    def run(
        self,
        max_messages: int | None = None,
        idle_timeout: float | None = None,
        report_every: int = 10,
    ) -> LoaderStats:
        idle_seconds = 0.0
        batch_size = self._settings.loader.batch_size
        log.info("loader started: batch_size=%s max_messages=%s", batch_size, max_messages)

        while not self._stopping:
            messages = self._consumer.consume(num_messages=batch_size, timeout=1.0)

            if not messages:
                idle_seconds += 1.0
                if self._limit_reached(max_messages):
                    break
                if idle_timeout and idle_seconds >= idle_timeout:
                    log.info("no messages for %.0fs, stopping", idle_seconds)
                    break
                self._consumer.poll(0)  # serve rebalance callbacks
                continue

            idle_seconds = 0.0
            self._handle_batch(messages)
            if report_every and self._stats.polls % report_every == 0:
                log.info(
                    "progress: polls=%s records=%s raw=%s dup=%s orders=%s dlq=%s late=%s",
                    self._stats.polls,
                    self._stats.records,
                    self._stats.raw_inserted,
                    self._stats.raw_duplicates,
                    self._stats.orders,
                    self._stats.dead_letters,
                    self._stats.late_events,
                )
            if self._limit_reached(max_messages):
                break

        self._shutdown()
        return self._stats

    def _shutdown(self) -> None:
        remaining = self._dlq.flush(10)
        if remaining:
            log.warning("%s dead letters still buffered at shutdown", remaining)
        self._consumer.close()
        try:
            self._warehouse.record_metric(
                "records_processed", float(self._stats.records), labels=dict(vars(self._stats))
            )
        except Exception as exc:  # noqa: BLE001 - metrics must never break shutdown
            log.debug("could not record final metrics: %s", exc)
        self._warehouse.close()
        log.info(
            "loader stopped: records=%s raw_inserted=%s raw_duplicates=%s orders=%s "
            "orders_ignored_stale=%s payments=%s customers=%s dead_letters=%s late_events=%s",
            self._stats.records,
            self._stats.raw_inserted,
            self._stats.raw_duplicates,
            self._stats.orders,
            self._stats.orders_ignored_stale,
            self._stats.payments,
            self._stats.customers,
            self._stats.dead_letters,
            self._stats.late_events,
        )

    # ---------------------------------------------------------------- batch
    def _handle_batch(self, messages: list[Message]) -> None:
        batch = Batch()
        payloads: dict[str, list[dict]] = {"orders": [], "payments": [], "customers": []}
        pending_dlq: list[tuple[Message, str, str]] = []
        watermarks: dict[str, dict] = {}
        now = datetime.now(timezone.utc)
        max_lateness = self._settings.loader.max_lateness_seconds

        for msg in messages:
            self._stats.records += 1

            error = msg.error()
            if error is not None:
                if error.code() == KafkaError._PARTITION_EOF:
                    continue
                pending_dlq.append((msg, "kafka_error", str(error)))
                batch.dead_letters.append(self._dlq_row(msg, "kafka_error", str(error)))
                continue

            topic = msg.topic()
            entity = self._settings.kafka.entity_for_topic(topic)

            try:
                decoded = decode_value(msg.value())
            except PayloadDecodeError as exc:
                pending_dlq.append((msg, DLQ_DESERIALIZATION, str(exc)))
                batch.dead_letters.append(self._dlq_row(msg, DLQ_DESERIALIZATION, str(exc)))
                continue

            payload = decoded.payload
            if entity is None:
                reason = f"no contract registered for topic {topic}"
                pending_dlq.append((msg, DLQ_VALIDATION, reason))
                batch.dead_letters.append(self._dlq_row(msg, DLQ_VALIDATION, reason))
                continue

            problems = validation_errors(entity, payload)
            if problems:
                reason = "; ".join(problems)[:900]
                pending_dlq.append((msg, DLQ_VALIDATION, reason))
                batch.dead_letters.append(self._dlq_row(msg, DLQ_VALIDATION, reason))
                continue

            event_time = parse_timestamp(payload.get("event_time"))
            if event_time is None:
                reason = f"unparsable event_time: {payload.get('event_time')!r}"
                pending_dlq.append((msg, DLQ_VALIDATION, reason))
                batch.dead_letters.append(self._dlq_row(msg, DLQ_VALIDATION, reason))
                continue

            key = msg.key().decode("utf-8", errors="replace") if msg.key() else None
            batch.raw_events.append(
                (
                    topic,
                    msg.partition(),
                    msg.offset(),
                    key,
                    payload.get("event_id"),
                    event_time,
                    Json(headers_to_dict(msg.headers())),
                    Json(payload),
                )
            )

            marks = watermarks.setdefault(
                topic, {"max_event_time": None, "max_ingested_at": now, "records": 0}
            )
            marks["records"] += 1
            if marks["max_event_time"] is None or event_time > marks["max_event_time"]:
                marks["max_event_time"] = event_time

            if is_late(event_time, max_lateness, now):
                batch.late_events.append(
                    (
                        topic,
                        msg.partition(),
                        msg.offset(),
                        payload.get("event_id"),
                        event_time,
                        lateness_seconds(event_time, now),
                        Json(payload),
                    )
                )
                continue

            payloads[entity].append(payload)

        # One round-trip per key per batch; the guard inside the upsert still
        # protects against an older event arriving in a later batch.
        for payload in latest_per_key(payloads["orders"], "order_id"):
            batch.orders.append(order_row(payload, parse_timestamp(payload["event_time"])))
        for payload in latest_per_key(payloads["payments"], "payment_id"):
            batch.payments.append(payment_row(payload, parse_timestamp(payload["event_time"])))
        for payload in latest_per_key(payloads["customers"], "customer_id"):
            batch.customers.append(customer_row(payload, parse_timestamp(payload["event_time"])))

        batch.watermarks = watermarks
        self._stats.polls += 1

        try:
            result = self._warehouse.write_batch(batch)
        except Exception:  # noqa: BLE001 - do not commit; let Kafka redeliver
            log.exception("warehouse write failed; offsets NOT committed, batch will be redelivered")
            return

        # Offsets move only after the data is durable.
        self._consumer.commit(asynchronous=False)

        for msg, error_class, error_message in pending_dlq:
            try:
                self._dlq.publish(msg, error_class, error_message)
            except Exception as exc:  # noqa: BLE001
                log.error("could not publish dead letter to Kafka: %s", exc)

        self._stats.absorb(result)
        log.debug("batch done: %s", result)

    @staticmethod
    def _dlq_row(msg: Message, error_class: str, error_message: str) -> tuple:
        value = msg.value()
        text = None if value is None else value.decode("utf-8", errors="replace")[:100_000]
        key = msg.key().decode("utf-8", errors="replace") if msg.key() else None
        return (
            msg.topic(),
            msg.partition(),
            msg.offset(),
            key,
            error_class,
            error_message[:2000],
            Json(headers_to_dict(msg.headers())),
            text,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consume Kafka events into the PostgreSQL warehouse.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--max-messages", type=int, default=None, help="stop after N records (CI / smoke tests)"
    )
    parser.add_argument(
        "--idle-timeout",
        type=float,
        default=None,
        help="stop after N seconds without messages (0 = run forever)",
    )
    parser.add_argument("--report-every", type=int, default=10, help="log progress every N batches")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)

    idle = args.idle_timeout if args.idle_timeout is not None else settings.loader.idle_timeout_seconds
    idle_timeout = None if idle <= 0 else idle

    loader = WarehouseLoader(settings)
    loader.run(max_messages=args.max_messages, idle_timeout=idle_timeout, report_every=args.report_every)
    return 0


if __name__ == "__main__":
    sys.exit(main())



