#!/usr/bin/env bash
# One-command end-to-end check: infra -> topics -> produce with faults -> load
# -> warehouse invariants -> dbt build -> lag report.
set -euo pipefail
cd "$(dirname "$0")/.."

test -f .env || cp .env.example .env

echo "==> 1/6 starting kafka, schema registry, kafka-ui, postgres"
docker compose up -d --build kafka schema-registry kafka-ui postgres

echo "==> 2/6 creating topics and registering schemas"
docker compose run --rm topics-init src.setup.init_topics
docker compose run --rm producer src.setup.register_schemas

echo "==> 3/6 producing 5000 events (5% duplicates, 2% late, 3% out of order, 0.1% malformed)"
docker compose run --rm producer src.producer.produce \
  --count 5000 --duplicate-rate 0.05 --late-rate 0.02 \
  --out-of-order-rate 0.03 --malformed-rate 0.001

echo "==> 4/6 loading until the topics are drained"
docker compose run --rm -e CONSUME_IDLE_TIMEOUT_SECONDS=5 stream-loader src.loader.consumer

echo "==> 5/6 checking warehouse invariants"
docker compose run --rm producer scripts.verify

echo "==> 6/6 building and testing the marts"
docker compose run --rm dbt-runner dbt build --project-dir dbt_project --profiles-dir dbt_project

echo "==> lag / freshness / dlq report"
docker compose run --rm producer src.monitoring.lag_report

echo
echo "kafka-ui:        http://localhost:8080"
echo "schema registry: http://localhost:8081"
echo "dashboard:       http://localhost:8501"
echo "warehouse psql:  docker compose exec postgres psql -U warehouse -d warehouse"
