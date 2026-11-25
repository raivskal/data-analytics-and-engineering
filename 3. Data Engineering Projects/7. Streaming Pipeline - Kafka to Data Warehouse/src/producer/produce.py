"""Publish synthetic events to Kafka with production-grade producer settings.

Every reliability knob here is deliberate:

``acks=all`` + ``enable.idempotence=true`` + retries
    no silent loss on broker failover, and retries cannot duplicate records;
``compression.type=zstd`` with ``linger.ms`` / ``batch.num.messages``
    throughput without hurting latency beyond the target;
message key = entity id
    ordering is only guaranteed per partition, so the key decides it.

Use ``--duplicate-rate`` / ``--late-rate`` / ``--out-of-order-rate`` /
``--malformed-rate`` to exercise the failure paths the loader must survive.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.serialization import MessageField, SerializationContext

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.common.schemas import EVENT_KEYS, EVENT_SCHEMAS, schema_json, validate_event
from src.producer.generate_events import EventFactory

log = get_logger(__name__)


def build_producer(bootstrap_servers: str) -> Producer:
    return Producer(
        {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "synthetic-producer",
            "acks": "all",
            "enable.idempotence": True,
            "compression.type": "zstd",
            "linger.ms": 20,
            "batch.num.messages": 10_000,
            "retries": 10,
            "max.in.flight.requests.per.connection": 5,
            "delivery.timeout.ms": 120_000,
        }
    )


def build_serializers() -> dict[str, JSONSerializer]:
    settings = get_settings()
    registry = SchemaRegistryClient({"url": settings.kafka.schema_registry_url})
    conf = {"auto.register.schemas": settings.kafka.auto_register_schemas}
    return {
        entity: JSONSerializer(schema_json(entity), registry, conf=conf) for entity in EVENT_SCHEMAS
    }



def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--count", type=int, default=1000, help="number of events to publish")
    parser.add_argument("--rate", type=float, default=0.0, help="events/second throttle (0 = as fast as possible)")
    parser.add_argument("--duplicate-rate", type=float, default=0.0, help="share of events sent twice")
    parser.add_argument("--late-rate", type=float, default=0.0, help="share of events backdated beyond the lateness limit")
    parser.add_argument("--out-of-order-rate", type=float, default=0.0, help="share of order events backdated slightly")
    parser.add_argument("--malformed-rate", type=float, default=0.0, help="share of events that break the contract")
    parser.add_argument("--late-seconds", type=int, default=7200, help="how far back late events are dated")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)

    factory = EventFactory(seed=args.seed)
    producer = build_producer(settings.kafka.bootstrap_servers)
    serializers = build_serializers()
    topics = settings.kafka.entity_topics()

    stats = {
        "sent": 0,
        "duplicates": 0,
        "late": 0,
        "out_of_order": 0,
        "malformed": 0,
        "delivered": 0,
        "failed": 0,
    }

    def on_delivery(err, msg) -> None:  # noqa: ANN001 - confluent callback signature
        if err is not None:
            stats["failed"] += 1
            log.error("delivery failed for %s[%s]: %s", msg.topic(), msg.partition(), err)
        else:
            stats["delivered"] += 1

    def publish(entity: str, payload: dict) -> None:
        topic = topics[entity]
        key = str(payload[EVENT_KEYS[entity]]).encode("utf-8")
        try:
            validate_event(entity, payload)
            value = serializers[entity](payload, SerializationContext(topic, MessageField.VALUE))
        except Exception as exc:  # noqa: BLE001 - deliberately injected faults land here
            # Publish un-framed JSON so the consumer hits a deserialization error
            # and dead-letters it: exactly what a broken upstream looks like.
            log.debug("publishing malformed payload for %s: %s", topic, exc)
            producer.produce(
                topic, key=key, value=json.dumps(payload).encode("utf-8"), on_delivery=on_delivery
            )
            stats["malformed"] += 1
            return
        producer.produce(topic, key=key, value=value, on_delivery=on_delivery)

    started = time.perf_counter()
    for index in range(args.count):
        entity, payload = factory.next_event()

        if args.out_of_order_rate and entity == "orders" and factory._rng.random() < args.out_of_order_rate:
            payload = factory.backdate(payload, seconds=factory._rng.randint(30, 120))
            stats["out_of_order"] += 1

        if args.late_rate and factory._rng.random() < args.late_rate:
            payload = factory.backdate(payload, seconds=args.late_seconds + factory._rng.randint(1, 600))
            stats["late"] += 1

        if args.malformed_rate and factory._rng.random() < args.malformed_rate:
            publish(entity, factory.corrupt(payload))
        else:
            publish(entity, payload)

        if args.duplicate_rate and factory._rng.random() < args.duplicate_rate:
            publish(entity, payload)  # same event_id, new offset -> collapsed downstream
            stats["duplicates"] += 1

        stats["sent"] += 1
        producer.poll(0)

        if args.rate > 0:
            target = started + (index + 1) / args.rate
            sleep_for = target - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)

    # flush() must always run before exit, otherwise buffered batches are lost.
    remaining = producer.flush(30)
    if remaining:
        log.error("%s messages still buffered after flush", remaining)
        return 1

    elapsed = time.perf_counter() - started
    log.info(
        "published %s events in %.1fs (%.0f/s): delivered=%s failed=%s duplicates=%s late=%s out_of_order=%s malformed=%s",
        stats["sent"],
        elapsed,
        stats["sent"] / elapsed if elapsed else 0.0,
        stats["delivered"],
        stats["failed"],
        stats["duplicates"],
        stats["late"],
        stats["out_of_order"],
        stats["malformed"],
    )
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
