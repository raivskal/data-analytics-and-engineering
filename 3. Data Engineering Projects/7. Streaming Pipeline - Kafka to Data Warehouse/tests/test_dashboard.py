"""Dashboard tests: pure formatters (unit) and the read-only query layer (integration).

The query tests exercise every SQL statement the dashboard renders, which is
where the real risk lives — a broken query shows up as an empty panel.
"""

import pytest

from src.common.config import get_settings
from src.monitoring import dashboard


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, "0"), (1_234, "1,234"), (None, "—"), ("12", "12"), ("not-a-number", "—")],
)
def test_fmt_int(value, expected):  # noqa: ANN001 - parametrized
    assert dashboard.fmt_int(value) == expected


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(None, "—"), (0.0, "0 s"), (45, "45 s"), (600, "10.0 min"), (7_200, "2.0 h"), (-5, "—")],
)
def test_fmt_age(seconds, expected):  # noqa: ANN001 - parametrized
    assert dashboard.fmt_age(seconds) == expected


def test_worst_freshness_handles_empty_and_nulls() -> None:
    import pandas as pd

    assert dashboard.worst_freshness(pd.DataFrame()) == 0.0
    frame = pd.DataFrame({"freshness_seconds": [10, None, 42]})
    assert dashboard.worst_freshness(frame) == 42.0


# --------------------------------------------------------------------- queries
@pytest.fixture(scope="module")
def dsn() -> str:
    settings = get_settings()
    try:
        dashboard.load_overview(settings.postgres.dsn)
    except Exception as exc:  # noqa: BLE001 - skip instead of failing without a stack
        pytest.skip(f"warehouse not reachable: {exc}")
    return settings.postgres.dsn


@pytest.mark.integration
def test_overview_exposes_every_dashboard_column(dsn: str) -> None:
    frame = dashboard.load_overview(dsn)
    expected = {
        "topic",
        "records",
        "distinct_events",
        "dead_letters",
        "dead_letters_open",
        "late_events",
        "max_event_time",
        "freshness_seconds",
    }
    assert expected <= set(frame.columns)


@pytest.mark.integration
def test_landing_counts_cover_all_entities(dsn: str) -> None:
    frame = dashboard.load_landing_counts(dsn)
    assert {"entity", "rows"} <= set(frame.columns)
    assert {"orders", "payments", "customers", "late_events", "dead_letters"} == set(frame["entity"])


@pytest.mark.integration
def test_dlq_frames_respect_the_limit(dsn: str) -> None:
    recent, by_class = dashboard.load_dlq(dsn, 10)
    assert len(recent) <= 10
    if not by_class.empty:
        assert {"error_class", "dead_letters"} <= set(by_class.columns)


@pytest.mark.integration
def test_late_events_and_coverage(dsn: str) -> None:
    late = dashboard.load_late(dsn, 5)
    assert len(late) <= 5
    coverage = dashboard.load_coverage(dsn)
    assert {"orders_in_landing", "orders_in_raw"} == set(coverage)


@pytest.mark.integration
def test_throughput_and_metric_history(dsn: str) -> None:
    throughput = dashboard.load_throughput(dsn)
    assert {"minute", "topic", "events"} <= set(throughput.columns)
    metrics = dashboard.load_metrics(dsn)
    assert {"recorded_at", "metric", "value"} <= set(metrics.columns)
