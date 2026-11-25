"""Live monitoring dashboard for the Kafka → warehouse pipeline.

Runs as its own Compose service (`dashboard`, port 8501) and answers the four
questions an on-call engineer actually asks:

1. **Is data flowing?** — throughput per minute and per topic, last record seen.
2. **Are we keeping up?** — consumer lag per partition (from Kafka) and freshness
   measured on event time (from `ops.watermarks`).
3. **What is broken?** — open dead letters with error class and message, plus
   quarantined late events.
4. **Is the warehouse consistent?** — raw vs landing coverage per entity.

All queries are read-only. Nothing here writes to Kafka or to the warehouse.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

import pandas as pd
import psycopg
import streamlit as st
from psycopg.rows import dict_row

from src.common.config import get_settings
from src.monitoring.lag_report import collect_lag

# --------------------------------------------------------------------------- SQL
TOPIC_OVERVIEW = """
WITH topics AS (
    SELECT DISTINCT topic FROM raw.events
    UNION SELECT DISTINCT topic FROM raw.dlq
    UNION SELECT DISTINCT topic FROM raw.late_events
    UNION SELECT topic FROM ops.watermarks
)
SELECT
    t.topic,
    (SELECT count(*) FROM raw.events e WHERE e.topic = t.topic)::int                      AS records,
    (SELECT count(DISTINCT e.event_id) FROM raw.events e WHERE e.topic = t.topic)::int      AS distinct_events,
    (SELECT count(*) FROM raw.dlq d WHERE d.topic = t.topic)::int                           AS dead_letters,
    (SELECT count(*) FROM raw.dlq d WHERE d.topic = t.topic AND d.replayed_at IS NULL)::int AS dead_letters_open,
    (SELECT count(*) FROM raw.late_events l WHERE l.topic = t.topic)::int                   AS late_events,
    w.max_event_time,
    w.max_ingested_at,
    extract(epoch FROM (now() - w.max_event_time))::double precision                        AS freshness_seconds
FROM topics t
LEFT JOIN ops.watermarks w ON w.topic = t.topic
ORDER BY t.topic
"""

THROUGHPUT = """
SELECT date_trunc('minute', ingested_at) AS minute, topic, count(*)::int AS events
FROM raw.events
GROUP BY 1, 2
ORDER BY 1
"""

LANDING_COUNTS = """
SELECT 'orders' AS entity, count(*)::int AS rows FROM landing.orders
UNION ALL SELECT 'payments', count(*)::int FROM landing.payments
UNION ALL SELECT 'customers', count(*)::int FROM landing.customers
UNION ALL SELECT 'late_events', count(*)::int FROM raw.late_events
UNION ALL SELECT 'dead_letters', count(*)::int FROM raw.dlq
ORDER BY entity
"""

DLQ_RECENT = """
SELECT failed_at, topic, partition_id, kafka_offset, message_key, error_class,
       left(error_message, 220) AS error_message, replayed_at
FROM raw.dlq
ORDER BY failed_at DESC
LIMIT %s
"""

DLQ_BY_CLASS = """
SELECT error_class, count(*)::int AS dead_letters
FROM raw.dlq
GROUP BY 1
ORDER BY 2 DESC
"""

LATE_RECENT = """
SELECT ingested_at, topic, partition_id, kafka_offset, event_time,
       round(lateness_seconds)::int AS lateness_seconds
FROM raw.late_events
ORDER BY ingested_at DESC
LIMIT %s
"""

COVERAGE = """
WITH order_events AS (
    SELECT count(DISTINCT payload ->> 'order_id')::int AS orders_in_raw
    FROM raw.events
    WHERE payload ->> 'order_id' IS NOT NULL
)
SELECT
    (SELECT count(*) FROM landing.orders)::int AS orders_in_landing,
    orders_in_raw
FROM order_events
"""

METRIC_HISTORY = """
SELECT recorded_at, metric, value::double precision AS value
FROM ops.pipeline_metrics
WHERE recorded_at > now() - interval '1 hour'
ORDER BY recorded_at
"""

LAG_WARN = 100
FRESHNESS_WARN_SECONDS = 900  # 15 min, matching the dbt source-freshness warning
# Auto-refresh can be disabled (DASHBOARD_AUTO_REFRESH=0) for headless render checks.
DEFAULT_AUTO_REFRESH = os.getenv("DASHBOARD_AUTO_REFRESH", "1").strip().lower() not in {"0", "false", "no"}


def main() -> None:
    st.set_page_config(
        page_title="Kafka → Warehouse monitor",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    settings = get_settings()
    dsn = settings.postgres.dsn

    with st.sidebar:
        st.header("Controls")
        auto_refresh = st.toggle("Auto-refresh", value=DEFAULT_AUTO_REFRESH)
        interval = st.slider("Refresh interval (seconds)", 2, 30, 5, disabled=not auto_refresh)
        detail_rows = st.slider("Detail rows", 10, 200, 50, step=10)
        st.divider()
        st.caption(f"consumer group · `{settings.loader.group_id}`")
        st.caption(f"warehouse · `{settings.postgres.host}:{settings.postgres.port}/{settings.postgres.database}`")
        st.caption(f"broker · `{settings.kafka.bootstrap_servers}`")
        if st.button("Reload now", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.caption(
            "Read-only. Lag comes from the broker, freshness from `ops.watermarks`, "
            "dead letters from `raw.dlq`."
        )

    st.title("📡 Kafka → Data Warehouse — live monitor")
    st.caption(
        f"Refreshed {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        + (f" · every {interval}s" if auto_refresh else " · manual")
    )

    try:
        overview = load_overview(dsn)
        lag = load_lag(settings.kafka.bootstrap_servers, settings.loader.group_id)
        landing = load_landing_counts(dsn)
        coverage = load_coverage(dsn)
    except Exception as exc:  # noqa: BLE001 - surface the problem instead of a stack trace
        st.error(f"Could not read monitoring data: {exc}")
        st.info("Is the stack up?  `docker compose up -d`  ·  is the loader running?")
        st.stop()

    landing_map = dict(zip(landing["entity"], landing["rows"])) if not landing.empty else {}
    total_records = int(pd.to_numeric(overview.get("records"), errors="coerce").fillna(0).sum())
    open_dlq = int(pd.to_numeric(overview.get("dead_letters_open"), errors="coerce").fillna(0).sum())
    late_total = int(pd.to_numeric(overview.get("late_events"), errors="coerce").fillna(0).sum())
    max_lag = int(lag["lag"].max()) if not lag.empty else 0
    total_lag = int(lag["lag"].sum()) if not lag.empty else 0
    freshness = worst_freshness(overview)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Raw records", fmt_int(total_records), help="Rows in raw.events (one per Kafka record)")
    k2.metric("Orders", fmt_int(landing_map.get("orders")), help="Current-state rows in landing.orders")
    k3.metric("Payments", fmt_int(landing_map.get("payments")))
    k4.metric(
        "Max partition lag",
        fmt_int(max_lag),
        delta=f"total {total_lag:,}",
        delta_color="inverse",
        help="Highest lag across partitions — an average would hide a stalled partition",
    )
    k5.metric("Open dead letters", fmt_int(open_dlq), help="raw.dlq rows not yet replayed")
    k6.metric("Worst freshness", fmt_age(freshness), help="Event time of the slowest topic vs now")

    problems = []
    if max_lag > LAG_WARN:
        problems.append(f"consumer lag {max_lag:,} exceeds {LAG_WARN:,}")
    if freshness > FRESHNESS_WARN_SECONDS:
        problems.append(f"freshness {fmt_age(freshness)} exceeds 15 min")
    if open_dlq:
        problems.append(f"{open_dlq:,} unreplayed dead letter(s)")

    if problems:
        st.warning("Attention — " + "; ".join(problems))
    else:
        st.success(f"All signals nominal · lag {total_lag:,} · freshness {fmt_age(freshness)}")

    tab_overview, tab_lag, tab_dlq, tab_late, tab_warehouse = st.tabs(
        ["📈 Throughput", "⏱️ Consumer lag", "☠️ Dead letters", "🕰️ Late events", "🏗️ Warehouse"]
    )

    # ---------------------------------------------------------------- throughput
    with tab_overview:
        st.subheader("Ingestion throughput")
        throughput = load_throughput(dsn)
        if throughput.empty:
            st.info("No records yet — publish some: `docker compose run --rm producer`")
        else:
            tp = throughput.copy()
            tp["minute"] = pd.to_datetime(tp["minute"], utc=True).dt.tz_localize(None)
            pivot = (
                tp.pivot_table(index="minute", columns="topic", values="events", aggfunc="sum")
                .fillna(0)
                .sort_index()
            )
            st.line_chart(pivot, height=320)
            st.caption(
                "Events ingested per minute and topic (`raw.events.ingested_at`). "
                "A line that flattens is a topic that stopped."
            )
            st.metric("Peak events per minute", fmt_int(int(pivot.sum(axis=1).max())))

        st.subheader("Per-topic health")
        if overview.empty:
            st.info("No topics have data yet.")
        else:
            st.dataframe(
                overview,
                width="stretch",
                hide_index=True,
                column_config={
                    "topic": "Topic",
                    "records": st.column_config.NumberColumn("Records", format="%d"),
                    "distinct_events": st.column_config.NumberColumn("Distinct", format="%d"),
                    "dead_letters": st.column_config.NumberColumn("Dead letters", format="%d"),
                    "dead_letters_open": st.column_config.NumberColumn("Open", format="%d"),
                    "late_events": st.column_config.NumberColumn("Late", format="%d"),
                    "max_event_time": st.column_config.DatetimeColumn("Watermark", format="HH:mm:ss"),
                    "max_ingested_at": st.column_config.DatetimeColumn("Last ingestion", format="HH:mm:ss"),
                    "freshness_seconds": st.column_config.NumberColumn("Freshness (s)", format="%.0f"),
                },
            )
            st.caption(
                "`Distinct` < `Records` means the producer delivered duplicates — collapsed "
                "downstream by the idempotent upsert, exactly as designed."
            )

    # ---------------------------------------------------------------------- lag
    with tab_lag:
        st.subheader("Consumer lag per partition")
        if lag.empty:
            st.info("No partitions visible for the consumer group yet.")
        else:
            lag_view = lag.copy()
            lag_view["partition_label"] = (
                lag_view["topic"].str.replace(r"\.(events|cdc)\.v\d+$", "", regex=True)
                + "[" + lag_view["partition"].astype(str) + "]"
            )
            st.bar_chart(lag_view.set_index("partition_label")["lag"], height=300)
            st.dataframe(
                lag_view[["topic", "partition", "committed", "high", "lag"]],
                width="stretch",
                hide_index=True,
            )
            worst = lag_view.sort_values("lag", ascending=False).iloc[0]
            if int(worst["lag"]) > 0:
                st.warning(
                    f"Largest backlog: {worst['topic']} — {int(worst['lag']):,} records behind"
                )
            st.caption(
                "Read from the broker for group `warehouse-loader`. One partition lagging while "
                "the rest sit at zero is the stalled-partition signature that averages hide."
            )

    # -------------------------------------------------------------- dead letters
    with tab_dlq:
        st.subheader("Dead letters")
        recent, by_class = load_dlq(dsn, detail_rows)
        if by_class.empty:
            st.success("No dead letters recorded.")
        else:
            left, right = st.columns([1, 2])
            with left:
                st.caption("By error class")
                st.bar_chart(by_class.set_index("error_class")["dead_letters"], height=240)
            with right:
                st.caption(f"Most recent {len(recent)} failures")
                st.dataframe(recent, width="stretch", hide_index=True, height=240)
            st.caption(
                "Each failure is also published to `<topic>.dlq` with `x-error-class`, "
                "`x-error-message` and `x-failed-at` headers, so triage does not require "
                "opening the payload."
            )

    # --------------------------------------------------------------- late events
    with tab_late:
        st.subheader("Late events (quarantined)")
        st.metric("Quarantined late events", fmt_int(late_total))
        late = load_late(dsn, detail_rows)
        if late.empty:
            st.success("Nothing outside the lateness window.")
        else:
            st.dataframe(late, width="stretch", hide_index=True)
            st.caption(
                f"Events older than MAX_LATENESS_SECONDS ({settings.loader.max_lateness_seconds}s) "
                "are quarantined here instead of being applied to current state — reconcile them "
                "deliberately rather than letting them silently rewrite history."
            )

    # ----------------------------------------------------------------- warehouse
    with tab_warehouse:
        st.subheader("Warehouse state")
        left, right = st.columns(2)
        with left:
            if not landing.empty:
                st.caption("Rows per table")
                st.bar_chart(landing.set_index("entity")["rows"], height=260)
        with right:
            in_raw = int(coverage.get("orders_in_raw") or 0)
            in_landing = int(coverage.get("orders_in_landing") or 0)
            st.metric("Distinct orders in raw.events", fmt_int(in_raw))
            st.metric("Orders in landing.orders", fmt_int(in_landing))
            if in_raw:
                st.caption(
                    f"Coverage {in_landing / in_raw:.1%}. The gap is late events awaiting "
                    "reconciliation plus orders whose newest event is still in flight."
                )

        st.subheader("Metrics history (last hour)")
        metrics = load_metrics(dsn)
        if metrics.empty:
            st.info("Run `src.monitoring.lag_report --write-metrics` to persist lag history.")
        else:
            m = metrics.copy()
            m["recorded_at"] = pd.to_datetime(m["recorded_at"], utc=True).dt.tz_localize(None)
            wide = m.pivot_table(index="recorded_at", columns="metric", values="value", aggfunc="last")
            st.line_chart(wide, height=260)

    st.divider()
    st.caption(
        "Queries are cached for a few seconds; **Reload now** clears the cache. "
        "Auto-refresh re-runs the script, so values are never more than one interval stale."
    )

    if auto_refresh:
        time.sleep(float(interval))
        st.rerun()





# ------------------------------------------------------------------------ data
@st.cache_resource
def get_connection(dsn: str) -> psycopg.Connection:
    """One read-only connection per Streamlit server process."""
    conn = psycopg.connect(dsn, autocommit=True, application_name="monitoring-dashboard")
    with conn.cursor() as cur:
        cur.execute("SET default_transaction_read_only = on")
    return conn


@st.cache_data(ttl=2, show_spinner=False)
def load_overview(dsn: str) -> pd.DataFrame:
    with get_connection(dsn).cursor(row_factory=dict_row) as cur:
        cur.execute(TOPIC_OVERVIEW)
        return pd.DataFrame(cur.fetchall())


@st.cache_data(ttl=2, show_spinner=False)
def load_throughput(dsn: str) -> pd.DataFrame:
    with get_connection(dsn).cursor(row_factory=dict_row) as cur:
        cur.execute(THROUGHPUT)
        return pd.DataFrame(cur.fetchall())


@st.cache_data(ttl=2, show_spinner=False)
def load_landing_counts(dsn: str) -> pd.DataFrame:
    with get_connection(dsn).cursor(row_factory=dict_row) as cur:
        cur.execute(LANDING_COUNTS)
        return pd.DataFrame(cur.fetchall())


@st.cache_data(ttl=2, show_spinner=False)
def load_dlq(dsn: str, limit: int = 50) -> tuple[pd.DataFrame, pd.DataFrame]:
    with get_connection(dsn).cursor(row_factory=dict_row) as cur:
        cur.execute(DLQ_RECENT, (limit,))
        recent = pd.DataFrame(cur.fetchall())
        cur.execute(DLQ_BY_CLASS)
        by_class = pd.DataFrame(cur.fetchall())
    return recent, by_class


@st.cache_data(ttl=2, show_spinner=False)
def load_late(dsn: str, limit: int = 50) -> pd.DataFrame:
    with get_connection(dsn).cursor(row_factory=dict_row) as cur:
        cur.execute(LATE_RECENT, (limit,))
        return pd.DataFrame(cur.fetchall())


@st.cache_data(ttl=2, show_spinner=False)
def load_coverage(dsn: str) -> dict:
    with get_connection(dsn).cursor(row_factory=dict_row) as cur:
        cur.execute(COVERAGE)
        return cur.fetchone() or {}


@st.cache_data(ttl=5, show_spinner=False)
def load_metrics(dsn: str) -> pd.DataFrame:
    with get_connection(dsn).cursor(row_factory=dict_row) as cur:
        cur.execute(METRIC_HISTORY)
        return pd.DataFrame(cur.fetchall())


@st.cache_data(ttl=3, show_spinner=False)
def load_lag(bootstrap_servers: str, group_id: str) -> pd.DataFrame:
    """Per-partition lag, read straight from the broker (never averaged)."""
    return pd.DataFrame(collect_lag(get_settings(), timeout=5))


# -------------------------------------------------------------------- helpers
def fmt_int(value: object) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


def fmt_age(seconds: object) -> str:
    try:
        total = float(seconds)
    except (TypeError, ValueError):
        return "—"
    if total != total or total < 0:  # NaN or event time in the future
        return "—"
    if total < 90:
        return f"{total:.0f} s"
    if total < 5400:
        return f"{total / 60:.1f} min"
    return f"{total / 3600:.1f} h"


def worst_freshness(overview: pd.DataFrame) -> float:
    if overview.empty or "freshness_seconds" not in overview:
        return 0.0
    series = pd.to_numeric(overview["freshness_seconds"], errors="coerce").dropna()
    return float(series.max()) if not series.empty else 0.0


if __name__ == "__main__":
    # `streamlit run` executes this file as __main__.
    main()

