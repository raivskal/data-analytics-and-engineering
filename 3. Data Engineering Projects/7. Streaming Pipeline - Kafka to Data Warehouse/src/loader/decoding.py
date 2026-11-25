"""Decode the Confluent Schema Registry wire format.

A schema-registry framed value looks like::

    byte 0      magic byte (0x00)
    bytes 1-4   schema id (big endian)
    bytes 5..   JSON payload

Decoding this explicitly (instead of using ``JSONDeserializer``) buys two
things for a warehouse loader:

* a message that is *not* framed can be recognised and dead-lettered as a
  deserialization error instead of crashing the poll loop;
* the raw bytes of a bad message can be forwarded to the DLQ untouched.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

MAGIC_BYTE = 0


class PayloadDecodeError(ValueError):
    """Raised when a record's value cannot be decoded into a JSON object."""


@dataclass(frozen=True)
class DecodedPayload:
    schema_id: int | None
    payload: dict


def decode_value(raw: bytes | None) -> DecodedPayload:
    """Return the schema id (if framed) and the parsed JSON object."""
    if raw is None:
        raise PayloadDecodeError("empty payload")

    schema_id: int | None = None
    body = raw
    if len(raw) > 5 and raw[0] == MAGIC_BYTE:
        schema_id = int.from_bytes(raw[1:5], "big")
        body = raw[5:]

    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PayloadDecodeError(f"payload is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise PayloadDecodeError(f"expected a JSON object, got {type(payload).__name__}")
    return DecodedPayload(schema_id=schema_id, payload=payload)
