"""Create the topics the pipeline needs, explicitly and idempotently.

Topic creation is deliberately *not* left to broker auto-creation: names,
partition counts, retention and cleanup policies belong in version control.

Usage:
    python -m src.setup.init_topics [--delete]
"""

from __future__ import annotations

import argparse
import sys

from confluent_kafka.admin import AdminClient, NewTopic

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger

log = get_logger(__name__)

# partitions chosen from expected throughput and the ordering unit (the message key)
TOPIC_SPECS: dict[str, dict] = {
    "orders": {
        "partitions": 6,
        "config": {"cleanup.policy": "delete", "retention.ms": str(7 * 24 * 60 * 60 * 1000)},
    },
    "payments": {
        "partitions": 3,
        "config": {"cleanup.policy": "delete", "retention.ms": str(7 * 24 * 60 * 60 * 1000)},
    },
    "customers": {
        # compacted: keeps the latest record per key, like a changelog
        "partitions": 3,
        "config": {"cleanup.policy": "compact", "retention.ms": str(30 * 24 * 60 * 60 * 1000)},
    },
}


def build_specs() -> list[NewTopic]:
    kafka = get_settings().kafka
    specs: list[NewTopic] = []
    for entity, topic in kafka.entity_topics().items():
        spec = TOPIC_SPECS[entity]
        specs.append(
            NewTopic(
                topic=topic,
                num_partitions=spec["partitions"],
                replication_factor=1,  # single-node local cluster
                config={**spec["config"], "min.insync.replicas": "1"},
            )
        )
        specs.append(
            NewTopic(
                topic=kafka.dlq_topic(topic),
                num_partitions=1,
                replication_factor=1,
                config={
                    "cleanup.policy": "delete",
                    "retention.ms": str(14 * 24 * 60 * 60 * 1000),
                    "min.insync.replicas": "1",
                },
            )
        )
    return specs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delete", action="store_true", help="delete the topics instead of creating them")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    admin = AdminClient({"bootstrap.servers": settings.kafka.bootstrap_servers})

    specs = build_specs()
    names = [topic for spec in specs for topic in [spec.topic]]

    if args.delete:
        for topic, future in admin.delete_topics(names).items():
            try:
                future.result()
                log.info("deleted topic %s", topic)
            except Exception as exc:  # noqa: BLE001 - report and continue
                log.warning("could not delete %s: %s", topic, exc)
        return 0

    existing = set(admin.list_topics(timeout=15).topics)
    to_create = [spec for spec in specs if spec.topic not in existing]
    for spec in specs:
        if spec.topic in existing:
            log.info("topic exists, leaving untouched: %s", spec.topic)

    if to_create:
        for topic, future in admin.create_topics(to_create).items():
            try:
                future.result()
                log.info("created topic %s", topic)
            except Exception as exc:  # noqa: BLE001
                log.error("failed to create %s: %s", topic, exc)
                return 1

    log.info("topics ready: %s", ", ".join(sorted(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
