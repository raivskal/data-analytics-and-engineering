"""Environment-driven configuration shared by the producer, loader and tooling.

Every setting can be overridden with an environment variable, which is how the
same code runs both inside Docker Compose (service DNS names) and in CI or on a
laptop (``localhost`` plus published ports).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote_plus

try:  # python-dotenv is convenient locally, but not required in containers
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - exercised only in minimal images
    pass


def _text(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw not in (None, "") else default


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class KafkaSettings:
    bootstrap_servers: str
    schema_registry_url: str
    auto_register_schemas: bool
    orders_topic: str
    payments_topic: str
    customers_topic: str
    dlq_suffix: str

    def dlq_topic(self, topic: str) -> str:
        """Dead-letter topic for a source topic (``orders.events.v1`` -> ``orders.events.v1.dlq``)."""
        return f"{topic}{self.dlq_suffix}"

    def entity_topics(self) -> dict[str, str]:
        return {
            "orders": self.orders_topic,
            "payments": self.payments_topic,
            "customers": self.customers_topic,
        }

    def entity_for_topic(self, topic: str) -> str | None:
        for entity, name in self.entity_topics().items():
            if name == topic:
                return entity
        return None


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    database: str
    user: str
    password: str

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass(frozen=True)
class LoaderSettings:
    group_id: str
    batch_size: int
    max_lateness_seconds: int
    idle_timeout_seconds: float


@dataclass(frozen=True)
class Settings:
    kafka: KafkaSettings
    postgres: PostgresSettings
    loader: LoaderSettings
    log_level: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read settings once per process."""
    kafka = KafkaSettings(
        bootstrap_servers=_text("KAFKA_BOOTSTRAP_SERVERS", "kafka:19092"),
        schema_registry_url=_text("SCHEMA_REGISTRY_URL", "http://schema-registry:8081"),
        auto_register_schemas=_bool("SCHEMA_AUTO_REGISTER", True),
        orders_topic=_text("TOPIC_ORDERS", "orders.events.v1"),
        payments_topic=_text("TOPIC_PAYMENTS", "payments.events.v1"),
        customers_topic=_text("TOPIC_CUSTOMERS", "customers.cdc.v1"),
        dlq_suffix=_text("DLQ_SUFFIX", ".dlq"),
    )
    postgres = PostgresSettings(
        host=_text("POSTGRES_HOST", "postgres"),
        port=_int("POSTGRES_PORT", 5432),
        database=_text("POSTGRES_DB", "warehouse"),
        user=_text("POSTGRES_USER", "warehouse"),
        password=_text("POSTGRES_PASSWORD", "warehouse"),
    )
    loader = LoaderSettings(
        group_id=_text("CONSUMER_GROUP", "warehouse-loader"),
        batch_size=_int("BATCH_SIZE", 500),
        max_lateness_seconds=_int("MAX_LATENESS_SECONDS", 3600),
        idle_timeout_seconds=float(_text("CONSUME_IDLE_TIMEOUT_SECONDS", "5")),
    )
    return Settings(
        kafka=kafka,
        postgres=postgres,
        loader=loader,
        log_level=_text("LOG_LEVEL", "INFO").upper(),
    )
