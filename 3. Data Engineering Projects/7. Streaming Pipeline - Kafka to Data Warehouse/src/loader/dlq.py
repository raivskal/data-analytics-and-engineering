"""Dead-letter publisher.

A DLQ entry is only useful if it carries enough context to act on, so the
original coordinates travel as headers:

``x-error-class``, ``x-error-message``, ``x-failed-at`` plus whatever headers
the producer attached (``trace-id``, ``source``...). The payload is forwarded
byte-for-byte so a fixed consumer or a replay job can reprocess it.
"""

from __future__ import annotations

from confluent_kafka import Message, Producer

from src.common.config import KafkaSettings
from src.loader.rules import dlq_headers, headers_to_dict


class DeadLetterPublisher:
    def __init__(self, settings: KafkaSettings) -> None:
        self._settings = settings
        self._producer = Producer(
            {
                "bootstrap.servers": settings.bootstrap_servers,
                "client.id": "warehouse-loader-dlq",
                "acks": "all",
                "enable.idempotence": True,
                "compression.type": "zstd",
                "linger.ms": 0,
            }
        )

    def publish(self, msg: Message, error_class: str, error_message: str) -> None:
        topic = self._settings.dlq_topic(msg.topic())
        headers = dlq_headers(headers_to_dict(msg.headers()), error_class, error_message)
        value = msg.value()
        self._producer.produce(
            topic=topic,
            key=msg.key() if msg.key() is not None else b"",
            value=value if value is not None else b"",
            headers=headers,
        )
        self._producer.poll(0)

    def flush(self, timeout: float = 10.0) -> int:
        return self._producer.flush(timeout)
