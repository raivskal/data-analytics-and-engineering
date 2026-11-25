"""End-to-end invariants, checked against a running docker compose stack.

Run with the stack up:  pytest -m integration
Skipped automatically when PostgreSQL is not reachable.
"""

import pytest

from src.common.config import get_settings
from src.loader.warehouse import Warehouse

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def warehouse() -> Warehouse:
    settings = get_settings()
    try:
        store = Warehouse(settings.postgres.dsn)
        store.health()
    except Exception as exc:  # noqa: BLE001 - the point is to skip, not to fail
        pytest.skip(f"warehouse not reachable: {exc}")
    yield store
    store.close()


def test_raw_layer_has_no_duplicate_offsets(warehouse: Warehouse) -> None:
    with warehouse._conn.cursor() as cur:
        cur.execute(
            "SELECT count(*), count(DISTINCT (topic, partition_id, kafka_offset)) FROM raw.events"
        )
        total, distinct = cur.fetchone()
    assert total > 0, "run the producer first"
    assert total == distinct


def test_landing_orders_are_unique_per_order(warehouse: Warehouse) -> None:
    with warehouse._conn.cursor() as cur:
        cur.execute("SELECT count(*), count(DISTINCT order_id) FROM landing.orders")
        total, distinct = cur.fetchone()
    assert total == distinct


def test_every_late_event_was_also_landed_raw(warehouse: Warehouse) -> None:
    with warehouse._conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*)
            FROM raw.late_events l
            LEFT JOIN raw.events e
                   ON e.topic = l.topic
                  AND e.partition_id = l.partition_id
                  AND e.kafka_offset = l.kafka_offset
            WHERE e.id IS NULL
            """
        )
        (orphans,) = cur.fetchone()
    assert orphans == 0


def test_dead_letters_record_an_error_class(warehouse: Warehouse) -> None:
    with warehouse._conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM raw.dlq WHERE error_class IS NULL OR error_class = ''")
        (unknown,) = cur.fetchone()
    assert unknown == 0


def test_watermarks_are_populated(warehouse: Warehouse) -> None:
    with warehouse._conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM ops.watermarks WHERE records_seen > 0")
        (topics,) = cur.fetchone()
    assert topics >= 1
