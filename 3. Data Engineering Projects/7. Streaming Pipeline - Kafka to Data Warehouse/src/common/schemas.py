"""Event contracts and validation helpers (JSON Schema draft-07).

Single source of truth for the message payloads:

* the producer validates before publishing,
* ``src.setup.register_schemas`` pre-registers them into Schema Registry,
* the loader validates every consumed record before it reaches the warehouse.

Unknown or invalid payloads are rejected here and routed to the dead-letter
topic instead of silently entering the raw layer.
"""

from __future__ import annotations

import json
from functools import lru_cache

SCHEMA_VERSION = 1

# Payload schema per logical entity.
EVENT_SCHEMAS: dict[str, dict] = {
    "orders": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "OrderEvent",
        "description": "Lifecycle event for an e-commerce order.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "event_id",
            "event_type",
            "event_time",
            "order_id",
            "customer_id",
            "store_id",
            "status",
            "currency",
            "amount",
            "item_count",
            "schema_version",
        ],
        "properties": {
            "event_id": {"type": "string", "minLength": 36, "maxLength": 36},
            "event_type": {
                "type": "string",
                "enum": ["order_created", "order_updated", "order_cancelled"],
            },
            "event_time": {"type": "string", "format": "date-time"},
            "order_id": {"type": "string", "pattern": "^ord_[0-9a-f]{12}$"},
            "customer_id": {"type": "string", "pattern": "^cus_[0-9a-f]{12}$"},
            "store_id": {"type": "integer", "minimum": 1},
            "status": {
                "type": "string",
                "enum": ["created", "paid", "shipped", "cancelled"],
            },
            "currency": {"type": "string", "enum": ["EUR", "USD"]},
            "amount": {"type": "number", "minimum": 0},
            "item_count": {"type": "integer", "minimum": 1},
            "schema_version": {"type": "integer", "const": SCHEMA_VERSION},
        },
    },
    "payments": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "PaymentEvent",
        "description": "Payment attempt and settlement events for an order.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "event_id",
            "event_time",
            "payment_id",
            "order_id",
            "method",
            "amount",
            "status",
            "schema_version",
        ],
        "properties": {
            "event_id": {"type": "string", "minLength": 36, "maxLength": 36},
            "event_time": {"type": "string", "format": "date-time"},
            "payment_id": {"type": "string", "pattern": "^pay_[0-9a-f]{12}$"},
            "order_id": {"type": "string", "pattern": "^ord_[0-9a-f]{12}$"},
            "method": {"type": "string", "enum": ["card", "paypal", "transfer"]},
            "amount": {"type": "number", "minimum": 0},
            "status": {
                "type": "string",
                "enum": ["authorized", "captured", "failed", "refunded"],
            },
            "schema_version": {"type": "integer", "const": SCHEMA_VERSION},
        },
    },
    "customers": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "CustomerEvent",
        "description": "Change event produced by the CRM for customer records.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "event_id",
            "event_time",
            "customer_id",
            "email",
            "full_name",
            "country",
            "segment",
            "op",
            "schema_version",
        ],
        "properties": {
            "event_id": {"type": "string", "minLength": 36, "maxLength": 36},
            "event_time": {"type": "string", "format": "date-time"},
            "customer_id": {"type": "string", "pattern": "^cus_[0-9a-f]{12}$"},
            "email": {"type": "string", "pattern": "^[^@\\s]+@[^@\\s]+\\.[A-Za-z]{2,}$"},
            "full_name": {"type": "string", "minLength": 1, "maxLength": 120},
            "country": {"type": "string", "pattern": "^[A-Z]{2}$"},
            "segment": {"type": "string", "enum": ["new", "returning", "vip"]},
            "op": {"type": "string", "enum": ["upsert", "delete"]},
            "schema_version": {"type": "integer", "const": SCHEMA_VERSION},
        },
    },
}

# Message key per entity: this is what guarantees per-entity ordering.
EVENT_KEYS: dict[str, str] = {
    "orders": "order_id",
    "payments": "order_id",
    "customers": "customer_id",
}


def schema_json(entity: str) -> str:
    """Schema as a JSON string, as expected by the serializers and the registry."""
    return json.dumps(EVENT_SCHEMAS[entity])


def subject_for_topic(topic: str) -> str:
    """Default ``TopicNameStrategy`` subject for message values."""
    return f"{topic}-value"


@lru_cache(maxsize=len(EVENT_SCHEMAS))
def _validator(entity: str):
    from jsonschema import Draft7Validator  # imported lazily: keeps tooling light

    return Draft7Validator(EVENT_SCHEMAS[entity])


def validate_event(entity: str, payload: dict) -> None:
    """Raise ``jsonschema.ValidationError`` if the payload violates the contract."""
    _validator(entity).validate(payload)


def validation_errors(entity: str, payload: object) -> list[str]:
    """Return human-readable errors instead of raising; used for dead-lettering."""
    errors = sorted(_validator(entity).iter_errors(payload), key=lambda err: list(err.path))
    return [f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in errors]
