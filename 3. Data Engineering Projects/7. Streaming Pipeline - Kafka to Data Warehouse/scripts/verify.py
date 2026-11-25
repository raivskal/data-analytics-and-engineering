"""Warehouse invariant checks — the "did it actually work?" script.

Run after producing and loading:

    docker compose run --rm producer scripts.verify

Exits non-zero if any invariant is violated, so it doubles as a CI gate.
"""

from __future__ import annotations

import sys

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.loader.warehouse import Warehouse

log = get_logger(__name__)

# Each check returns rows only when something is wrong.
CHECKS: list[tuple[str, str]] = [
    (
        "raw.events has duplicate offsets",
        """
        SELECT topic, partition_id, kafka_offset, count(*) AS rows
        FROM raw.events
        GROUP BY 1, 2, 3
        HAVING count(*) > 1
        """,
    ),
    (
        "landing.orders has duplicate order_id",
        """
        SELECT order_id, count(*) AS rows
        FROM landing.orders
        GROUP BY 1
        HAVING count(*) > 1
        """,
    ),
    (
        "landing.orders rows without a matching raw event",
        """
        SELECT o.order_id
        FROM landing.orders o
        WHERE NOT EXISTS (
            SELECT 1 FROM raw.events e WHERE e.payload ->> 'order_id' = o.order_id
        )
        """,
    ),
    (
        "late events that were never landed in raw.events",
        """
        SELECT l.topic, l.partition_id, l.kafka_offset
        FROM raw.late_events l
        LEFT JOIN raw.events e
               ON e.topic = l.topic
              AND e.partition_id = l.partition_id
              AND e.kafka_offset = l.kafka_offset
        WHERE e.id IS NULL
        """,
    ),
    (
        "dead letters without an error class",
        """
        SELECT id FROM raw.dlq WHERE coalesce(error_class, '') = ''
        """,
    ),
]


def main() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)

    with Warehouse(settings.postgres.dsn) as warehouse:
        health = warehouse.health()
        print("\npipeline health")
        print("-" * 40)
        for key, value in health.items():
            print(f"  {key:<24} {value}")

        failures = 0
        print("\ninvariants")
        print("-" * 40)
        with warehouse._conn.cursor() as cur:  # noqa: SLF001 - operator tool
            for label, sql in CHECKS:
                cur.execute(sql)
                rows = cur.fetchall()
                if rows:
                    failures += 1
                    log.error("FAIL %s (%s rows, first: %s)", label, len(rows), rows[0])
                else:
                    print(f"  ok   {label}")

            # Only meaningful once dbt has built the marts.
            cur.execute("SELECT to_regclass('marts.fct_orders') IS NOT NULL")
            if cur.fetchone()[0]:
                cur.execute(
                    "SELECT order_id, count(*) FROM marts.fct_orders GROUP BY 1 HAVING count(*) > 1"
                )
                duplicates = cur.fetchall()
                if duplicates:
                    failures += 1
                    log.error("FAIL marts.fct_orders has duplicate order_id: %s", duplicates[:3])
                else:
                    print("  ok   marts.fct_orders is unique per order")

    if failures:
        log.error("%s invariant(s) violated", failures)
        return 1
    log.info("all invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
