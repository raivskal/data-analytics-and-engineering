"""Pre-register the event schemas in Schema Registry (the CI governance gate).

In production you do not let clients auto-register schemas: the contract is
reviewed and registered deliberately, with an explicit compatibility level, and
producers run with ``auto.register.schemas=false``. This script is that step.

Usage:
    python -m src.setup.register_schemas [--compatibility BACKWARD]
"""

from __future__ import annotations

import argparse
import sys

from confluent_kafka.schema_registry import Schema, SchemaRegistryClient
from confluent_kafka.schema_registry.error import SchemaRegistryError

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.common.schemas import EVENT_SCHEMAS, schema_json, subject_for_topic

log = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compatibility",
        default="BACKWARD",
        choices=["BACKWARD", "BACKWARD_TRANSITIVE", "FORWARD", "FULL", "NONE"],
        help="compatibility level applied to every subject",
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    client = SchemaRegistryClient({"url": settings.kafka.schema_registry_url})

    exit_code = 0
    for entity, topic in settings.kafka.entity_topics().items():
        subject = subject_for_topic(topic)
        schema = Schema(schema_json(entity), schema_type="JSON")
        try:
            client.set_compatibility(subject_name=subject, level=args.compatibility)
        except SchemaRegistryError as exc:  # older registry versions differ slightly
            log.debug("could not set compatibility for %s: %s", subject, exc)
        try:
            schema_id = client.register_schema(subject, schema)
            log.info("registered %s (id=%s, compatibility=%s)", subject, schema_id, args.compatibility)
        except SchemaRegistryError as exc:
            log.error("failed to register %s: %s", subject, exc)
            exit_code = 1

    # Surfaces the stored contract, which is what consumers will resolve.
    for subject in client.get_subjects():
        if subject.endswith("-value"):
            version = client.get_latest_version(subject)
            log.info("subject %s -> version %s", subject, version.version)

    if len(EVENT_SCHEMAS) != len(settings.kafka.entity_topics()):
        log.warning("schema definitions and configured topics are out of sync")
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
