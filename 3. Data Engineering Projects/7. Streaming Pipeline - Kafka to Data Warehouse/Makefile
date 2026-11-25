# Convenience wrapper around docker compose. `make help` lists the targets.
SHELL := /bin/sh
COMPOSE := docker compose
APP := docker compose run --rm -e CONSUME_IDLE_TIMEOUT_SECONDS=5

.PHONY: help env up down clean topics produce load dbt test lint lag verify logs ps dashboard

help:
	@echo "make up        start kafka + schema registry + kafka-ui + postgres, topics, loader, dbt loop, dashboard"
	@echo "make env       create .env from .env.example (if missing)"
	@echo "make produce   publish 5000 events with duplicates / late / out-of-order / malformed"
	@echo "make load      run the loader until the topic is drained"
	@echo "make dbt       run dbt build once"
	@echo "make dashboard open the monitoring dashboard (http://localhost:8501)"
	@echo "make test      unit tests (no broker needed)"
	@echo "make lint      ruff"
	@echo "make lag       per-partition lag / freshness / dlq report"
	@echo "make verify    assert idempotency invariants in the warehouse"
	@echo "make down      stop everything (keeps volumes)"
	@echo "make clean     stop everything and delete the Kafka + Postgres volumes"

env:
	@test -f .env || cp .env.example .env

up: env
	$(COMPOSE) up -d --build kafka schema-registry kafka-ui postgres
	$(COMPOSE) up -d topics-init
	$(COMPOSE) up -d stream-loader dbt-runner dashboard
	@echo "dashboard http://localhost:8501  kafka-ui http://localhost:8080  schema-registry http://localhost:8081"

dashboard: env
	$(COMPOSE) up -d dashboard
	@echo "dashboard http://localhost:8501"

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

topics: env
	$(COMPOSE) run --rm topics-init

produce: env
	$(COMPOSE) run --rm producer src.producer.produce --count 5000 --duplicate-rate 0.05 --late-rate 0.02 --out-of-order-rate 0.03 --malformed-rate 0.001

load: env
	$(APP) stream-loader src.loader.consumer

dbt: env
	$(COMPOSE) run --rm dbt-runner dbt build --project-dir dbt_project --profiles-dir dbt_project

test:
	$(COMPOSE) run --rm -e CONSUME_IDLE_TIMEOUT_SECONDS=5 producer pytest -m "not integration" -q

lint:
	$(COMPOSE) run --rm producer ruff check src tests

lag: env
	$(COMPOSE) run --rm producer src.monitoring.lag_report --write-metrics

verify: env
	$(COMPOSE) run --rm producer scripts.verify

schemas: env
	$(COMPOSE) run --rm producer src.setup.register_schemas

logs:
	$(COMPOSE) logs -f stream-loader dbt-runner

ps:
	$(COMPOSE) ps
