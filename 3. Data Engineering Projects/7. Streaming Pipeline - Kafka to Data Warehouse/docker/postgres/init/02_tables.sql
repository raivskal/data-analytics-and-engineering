-- =========================================================================
-- raw: append-only, replayable landing zone
-- =========================================================================
CREATE TABLE IF NOT EXISTS raw.events (
    id           BIGSERIAL   PRIMARY KEY,
    topic        TEXT        NOT NULL,
    partition_id INTEGER     NOT NULL,
    kafka_offset BIGINT      NOT NULL,
    message_key  TEXT,
    event_id     TEXT,
    event_time   TIMESTAMPTZ,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    headers      JSONB       NOT NULL DEFAULT '{}'::jsonb,
    payload      JSONB       NOT NULL,
    -- The idempotency key of the ingestion itself: one row per Kafka record.
    CONSTRAINT raw_events_unique_offset UNIQUE (topic, partition_id, kafka_offset)
);

CREATE INDEX IF NOT EXISTS raw_events_topic_event_time_idx ON raw.events (topic, event_time);
CREATE INDEX IF NOT EXISTS raw_events_event_id_idx        ON raw.events (event_id);
CREATE INDEX IF NOT EXISTS raw_events_ingested_at_idx     ON raw.events (ingested_at);

CREATE TABLE IF NOT EXISTS raw.dlq (
    id            BIGSERIAL   PRIMARY KEY,
    topic         TEXT        NOT NULL,
    partition_id  INTEGER     NOT NULL,
    kafka_offset  BIGINT      NOT NULL,
    message_key   TEXT,
    error_class   TEXT        NOT NULL,
    error_message TEXT        NOT NULL,
    headers       JSONB       NOT NULL DEFAULT '{}'::jsonb,
    payload       TEXT,
    failed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    replayed_at   TIMESTAMPTZ,
    -- replays must not duplicate the quarantine record either
    CONSTRAINT raw_dlq_unique_offset UNIQUE (topic, partition_id, kafka_offset)
);

CREATE INDEX IF NOT EXISTS raw_dlq_topic_failed_at_idx ON raw.dlq (topic, failed_at);
CREATE INDEX IF NOT EXISTS raw_dlq_unreplayed_idx      ON raw.dlq (failed_at) WHERE replayed_at IS NULL;

CREATE TABLE IF NOT EXISTS raw.late_events (
    id                BIGSERIAL   PRIMARY KEY,
    topic             TEXT        NOT NULL,
    partition_id      INTEGER     NOT NULL,
    kafka_offset      BIGINT      NOT NULL,
    event_id          TEXT,
    event_time        TIMESTAMPTZ,
    lateness_seconds  NUMERIC(12, 3) NOT NULL,
    payload           JSONB       NOT NULL,
    ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT raw_late_events_unique_offset UNIQUE (topic, partition_id, kafka_offset)
);

CREATE INDEX IF NOT EXISTS raw_late_events_event_time_idx ON raw.late_events (event_time);

-- =========================================================================
-- landing: current state per entity (upsert target, mirrors Kafka Connect
-- JDBC sink with insert.mode=upsert / pk.mode=record_key)
-- =========================================================================
CREATE TABLE IF NOT EXISTS landing.orders (
    order_id     TEXT          PRIMARY KEY,
    customer_id  TEXT          NOT NULL,
    store_id     INTEGER,
    status       TEXT          NOT NULL,
    currency     CHAR(3)       NOT NULL,
    order_amount NUMERIC(12,2) NOT NULL,
    item_count   INTEGER       NOT NULL,
    event_id     TEXT          NOT NULL,
    event_time   TIMESTAMPTZ   NOT NULL,
    updated_at   TIMESTAMPTZ   NOT NULL,
    ingested_at  TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS landing_orders_event_time_idx  ON landing.orders (event_time);
CREATE INDEX IF NOT EXISTS landing_orders_customer_id_idx ON landing.orders (customer_id);

CREATE TABLE IF NOT EXISTS landing.payments (
    payment_id TEXT          PRIMARY KEY,
    order_id   TEXT          NOT NULL,
    method     TEXT          NOT NULL,
    amount     NUMERIC(12,2) NOT NULL,
    status     TEXT          NOT NULL,
    event_id   TEXT          NOT NULL,
    event_time TIMESTAMPTZ   NOT NULL,
    updated_at TIMESTAMPTZ   NOT NULL
);

CREATE INDEX IF NOT EXISTS landing_payments_order_id_idx ON landing.payments (order_id);

CREATE TABLE IF NOT EXISTS landing.customers (
    customer_id TEXT        PRIMARY KEY,
    email       TEXT,
    full_name   TEXT,
    country     CHAR(2),
    segment     TEXT,
    is_deleted  BOOLEAN     NOT NULL DEFAULT false,
    event_id    TEXT        NOT NULL,
    event_time  TIMESTAMPTZ NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL
);

-- =========================================================================
-- ops: watermarks and pipeline metrics
-- =========================================================================
CREATE TABLE IF NOT EXISTS ops.watermarks (
    topic           TEXT        PRIMARY KEY,
    max_event_time  TIMESTAMPTZ,
    max_ingested_at TIMESTAMPTZ,
    records_seen    BIGINT      NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.pipeline_metrics (
    id          BIGSERIAL   PRIMARY KEY,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metric      TEXT        NOT NULL,
    topic       TEXT,
    value       NUMERIC(18,3) NOT NULL,
    labels      JSONB       NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ops_pipeline_metrics_metric_idx ON ops.pipeline_metrics (metric, recorded_at);

-- Convenience view used by the README verification steps and scripts/verify.sh.
CREATE OR REPLACE VIEW ops.pipeline_health AS
SELECT
    (SELECT count(*) FROM raw.events)                        AS raw_events,
    (SELECT count(DISTINCT event_id) FROM raw.events)        AS distinct_events,
    (SELECT count(*) FROM landing.orders)                     AS landing_orders,
    (SELECT count(*) FROM landing.payments)                   AS landing_payments,
    (SELECT count(*) FROM landing.customers)                  AS landing_customers,
    (SELECT count(*) FROM raw.late_events)                    AS late_events,
    (SELECT count(*) FROM raw.dlq)                            AS dead_letters,
    (SELECT max(max_event_time) FROM ops.watermarks)          AS watermark_event_time;
