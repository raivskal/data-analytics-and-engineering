-- Schema layout for the streaming warehouse.
--   raw      immutable, replayable landing zone (one row per Kafka record)
--   landing  current state per entity, maintained with idempotent upserts
--   staging  dbt staging models (typed / cleaned views)
--   marts    dbt marts (facts, dimensions, aggregates)
--   snapshots dbt SCD2 snapshots
--   ops      pipeline metadata: watermarks, metrics

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS landing;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS snapshots;
CREATE SCHEMA IF NOT EXISTS ops;

COMMENT ON SCHEMA raw       IS 'Append-only copy of every consumed Kafka record, replayable.';
COMMENT ON SCHEMA landing   IS 'Entity state after applying events, written with idempotent upserts.';
COMMENT ON SCHEMA staging   IS 'dbt staging layer: typed, cleaned, one row per key.';
COMMENT ON SCHEMA marts     IS 'dbt marts: facts, dimensions and aggregates.';
COMMENT ON SCHEMA snapshots IS 'dbt snapshots (SCD2 history).';
COMMENT ON SCHEMA ops       IS 'Operational metadata: watermarks, pipeline metrics.';
