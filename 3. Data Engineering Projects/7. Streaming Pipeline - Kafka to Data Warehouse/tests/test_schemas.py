import json

import pytest
from jsonschema import ValidationError

from src.common.schemas import (
    EVENT_KEYS,
    EVENT_SCHEMAS,
    schema_json,
    subject_for_topic,
    validate_event,
    validation_errors,
)
from src.producer.generate_events import EventFactory


@pytest.fixture(scope="module")
def factory() -> EventFactory:
    return EventFactory(seed=7)


@pytest.mark.parametrize("kind", ["order_new", "order_update", "payment", "customer"])
def test_generated_events_match_the_contract(factory: EventFactory, kind: str) -> None:
    entity, payload = factory.next_event(kind)
    assert entity in EVENT_SCHEMAS
    validate_event(entity, payload)  # raises on violation


def test_every_schema_is_valid_json_schema() -> None:
    for entity, schema in EVENT_SCHEMAS.items():
        parsed = json.loads(schema_json(entity))
        assert parsed["title"]
        assert parsed["required"], entity
        # the version field is pinned by the contract
        assert parsed["properties"]["schema_version"]["const"] == 1


def test_message_key_is_part_of_every_payload(factory: EventFactory) -> None:
    for entity in EVENT_SCHEMAS:
        _, payload = factory.next_event(
            {"orders": "order_new", "payments": "payment", "customers": "customer"}[entity]
        )
        assert EVENT_KEYS[entity] in payload


def test_corrupted_event_is_rejected(factory: EventFactory) -> None:
    _, payload = factory.next_event("order_new")
    broken = factory.corrupt(payload)
    errors = validation_errors("orders", broken)
    assert errors, "a corrupted payload must produce validation errors"
    with pytest.raises(ValidationError):
        validate_event("orders", broken)


def test_unknown_topic_maps_to_the_default_subject() -> None:
    assert subject_for_topic("orders.events.v1") == "orders.events.v1-value"
