"""Operational report: consumer lag, freshness and dead-letter volume.

Alerting guidance baked into the numbers here:

* lag is reported **per partition** and summarised with ``max()`` — an average
  hides the one stalled partition that actually breaks an SLO;
* freshness is measured on ``event_time`` (data time) not on bytes moved;
* dead letters are reported as a count *and* a rate, because a small steady
  trickle is normal while a spike means an upstream contract change.

Usage:
    python -m src.monitoring.lag_report [--fail-on-lag 1000] [--write-metrics]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from confluent_kafka import Consumer, TopicPartition

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.loader.warehouse import Warehouse

log = get_logger(__name__)


def collect_lag(settings, timeout: float = 10.0) -> list[dict]:
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka.bootstrap_servers,
            "group.id": settings.loader.group_id,
            "enable.auto.commit": False,
        }
    )
    rows: list[dict] = []
    try:
        for topic in settings.kafka.entity_topics().values():
            metadata = consumer.list_topics(topic=topic, timeout=timeout)
            partitions = metadata.topics[topic].partitions
            requests = [TopicPartition(topic, partition) for partition in sorted(partitions)]
            committed = {tp.partition: tp.offset for tp in consumer.committed(requests, timeout=timeout)}
            for tp in requests:
                low, high = consumer.get_watermark_offsets(tp, timeout=timeout, cached=False)
                position = committed.get(tp.partition, -1001)
                # -1001 == no committed offset yet, -1 == unavailable
                effective = position if position is not None and position >= 0 else low
                rows.append(
                    {
                        "topic": tp.topic,
                        "partition": tp.partition,
                        "committed": effective,
                        "high": high,
                        "lag": max(high - effective, 0),
                    }
                )
    finally:
        consumer.close()
    return rows


def freshness(warehouse: Warehouse) -> list[tuple[str, float | None]]:
    with warehouse._conn.cursor() as cur:  # noqa: SLF001 - monitoring is a trusted operator tool
        cur.execute("SELECT topic, max_event_time, records_seen FROM ops.watermarks ORDER BY topic")
        rows = cur.fetchall()
    now = datetime.now(timezone.utc)
    return [
        (topic, (now - event_time).total_seconds() if event_time else None, records)
        for topic, event_time, records in rows
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fail-on-lag", type=int, default=None, help="exit 1 when max lag exceeds this")
    parser.add_argument("--write-metrics", action="store_true", help="persist the numbers to ops.pipeline_metrics")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)

    lag_rows = collect_lag(settings)
    print(f"\n{'topic':<24}{'partition':>10}{'committed':>12}{'high':>12}{'lag':>8}")
    print("-" * 66)
    for row in lag_rows:
        print(
            f"{row['topic']:<24}{row['partition']:>10}{row['committed']:>12}{row['high']:>12}{row['lag']:>8}"
        )

    max_lag = max((row["lag"] for row in lag_rows), default=0)
    total_lag = sum(row["lag"] for row in lag_rows)
    print("-" * 66)
    print(f"total lag: {total_lag}   max partition lag: {max_lag}")

    with Warehouse(settings.postgres.dsn) as warehouse:
        print(f"\n{'topic':<24}{'freshness_s':>14}{'watermark records':>20}")
        print("-" * 58)
        for topic, seconds, records in freshness(warehouse):
            shown = "n/a" if seconds is None else f"{seconds:.0f}"
            print(f"{topic:<24}{shown:>14}{records:>20}")

        health = warehouse.health()
        print("\npipeline health:")
        for key, value in health.items():
            print(f"  {key:<24} {value}")

        if args.write_metrics:
            warehouse.record_metric("consumer_lag_total", float(total_lag))
            warehouse.record_metric("consumer_lag_max", float(max_lag))
            warehouse.record_metric("dead_letters_total", float(health.get("dead_letters") or 0))

    if args.fail_on_lag is not None and max_lag > args.fail_on_lag:
        log.error("max partition lag %s exceeds limit %s", max_lag, args.fail_on_lag)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
