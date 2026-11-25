"""Deterministic synthetic event generator.

Produces realistic order / payment / customer events so the pipeline can be
exercised end to end without an external source system. Being seeded, the same
``--seed`` always yields the same stream, which makes the integration checks in
CI reproducible.

The generator also exposes the failure modes a streaming pipeline must cope
with, so they can be demonstrated deliberately:

* duplicate events (at-least-once delivery / producer retries)
* late events (event_time far behind wall-clock time)
* out-of-order events (an older event arrives for a key after a newer one)
* malformed events (violating the schema contract)
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from src.common.schemas import SCHEMA_VERSION

CUSTOMER_POOL_SIZE = 200
STORE_POOL_SIZE = 12
PAYMENT_METHODS = ("card", "paypal", "transfer")
SEGMENTS = ("new", "returning", "vip")
COUNTRIES = ("DE", "FR", "NL", "LV", "EE", "LT", "PL", "ES", "IT")
FIRST_NAMES = ("Anna", "Ralfs", "Marta", "Jaan", "Lukas", "Sofia", "Emils", "Nora", "Karlis", "Elena")
LAST_NAMES = ("Berzina", "Kalnins", "Ojala", "Novak", "Petrov", "Laine", "Silva", "Kask", "Vilks", "Saar")


def _hex(rng: random.Random, length: int = 12) -> str:
    return f"{rng.getrandbits(4 * length):0{length}x}"


def _uuid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass
class EventFactory:
    """Creates valid payloads plus, on request, deliberately invalid ones."""

    seed: int = 42
    start_time: datetime | None = None
    _rng: random.Random = field(init=False, repr=False)
    _customers: list[str] = field(init=False, default_factory=list)
    _open_orders: list[dict] = field(init=False, default_factory=list)
    _clock: datetime = field(init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        # Start just behind wall-clock time so normal events are inside the
        # lateness window; late/faulty events are then backdated explicitly.
        self._clock = self.start_time or (datetime.now(timezone.utc) - timedelta(minutes=5))
        self._customers = [f"cus_{_hex(self._rng)}" for _ in range(CUSTOMER_POOL_SIZE)]

    # ------------------------------------------------------------------ clock
    def _tick(self) -> datetime:
        """Advance a virtual clock so event_time is sensible and never in the future."""
        self._clock += timedelta(seconds=self._rng.uniform(0.01, 0.25))
        now = datetime.now(timezone.utc)
        if self._clock > now:
            self._clock = now
        return self._clock

    # ----------------------------------------------------------------- writer
    def next_event(self, kind: str | None = None) -> tuple[str, dict]:
        """Return ``(entity, payload)`` where entity is orders|payments|customers."""
        kind = kind or self._weighted_kind()
        if kind == "order_new":
            return "orders", self.order_created()
        if kind == "order_update":
            if not self._open_orders:
                return "orders", self.order_created()
            return "orders", self.order_updated()
        if kind == "payment":
            return "payments", self.payment()
        if kind == "customer":
            return "customers", self.customer_event()
        raise ValueError(f"unknown event kind: {kind}")

    def _weighted_kind(self) -> str:
        roll = self._rng.random()
        if roll < 0.55:
            return "order_new"
        if roll < 0.75:
            return "order_update"
        if roll < 0.92:
            return "payment"
        return "customer"

    # ----------------------------------------------------------------- events
    def order_created(self, event_time: datetime | None = None) -> dict:
        ts = event_time or self._tick()
        item_count = self._rng.randint(1, 4)
        amount = round(sum(self._rng.uniform(5, 250) for _ in range(item_count)), 2)
        order = {
            "order_id": f"ord_{_hex(self._rng)}",
            "customer_id": self._rng.choice(self._customers),
            "amount": amount,
            "item_count": item_count,
        }
        self._open_orders.append(order)
        return {
            "event_id": _uuid(self._rng),
            "event_type": "order_created",
            "event_time": _iso(ts),
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "store_id": self._rng.randint(1, STORE_POOL_SIZE),
            "status": "created",
            "currency": self._rng.choice(("EUR", "EUR", "USD")),
            "amount": amount,
            "item_count": item_count,
            "schema_version": SCHEMA_VERSION,
        }

    def order_updated(self) -> dict:
        """Transition an open order to paid / shipped / cancelled."""
        order = self._rng.choice(self._open_orders)
        status = self._rng.choice(("paid", "shipped", "cancelled"))
        if status == "cancelled":
            self._open_orders.remove(order)
        return {
            "event_id": _uuid(self._rng),
            "event_type": "order_cancelled" if status == "cancelled" else "order_updated",
            "event_time": _iso(self._tick()),
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "store_id": self._rng.randint(1, STORE_POOL_SIZE),
            "status": status,
            "currency": "EUR",
            "amount": order["amount"],
            "item_count": order["item_count"],
            "schema_version": SCHEMA_VERSION,
        }

    def payment(self) -> dict:
        order = self._rng.choice(self._open_orders) if self._open_orders else None
        return {
            "event_id": _uuid(self._rng),
            "event_time": _iso(self._tick()),
            "payment_id": f"pay_{_hex(self._rng)}",
            "order_id": order["order_id"] if order else f"ord_{_hex(self._rng)}",
            "method": self._rng.choice(PAYMENT_METHODS),
            "amount": order["amount"] if order else 0.0,
            "status": self._rng.choice(("authorized", "captured", "captured", "failed")),
            "schema_version": SCHEMA_VERSION,
        }

    def customer_event(self) -> dict:
        customer_id = self._rng.choice(self._customers)
        name = f"{self._rng.choice(FIRST_NAMES)} {self._rng.choice(LAST_NAMES)}"
        return {
            "event_id": _uuid(self._rng),
            "event_time": _iso(self._tick()),
            "customer_id": customer_id,
            "email": f"{name.split()[0].lower()}.{_hex(self._rng, 6)}@example.com",
            "full_name": name,
            "country": self._rng.choice(COUNTRIES),
            "segment": self._rng.choice(SEGMENTS),
            "op": "upsert" if self._rng.random() > 0.05 else "delete",
            "schema_version": SCHEMA_VERSION,
        }

    # -------------------------------------------------------------- fault modes
    def backdate(self, payload: dict, seconds: int) -> dict:
        """Return a copy whose event_time is ``seconds`` earlier (late / out-of-order)."""
        clone = dict(payload)
        original = datetime.fromisoformat(clone["event_time"].replace("Z", "+00:00"))
        clone["event_time"] = _iso(original - timedelta(seconds=seconds))
        return clone

    def corrupt(self, payload: dict) -> dict:
        """Break the contract in a way the schema must reject."""
        broken = dict(payload)
        if "amount" in broken:
            broken["amount"] = -1
        if "status" in broken:
            broken["status"] = "definitely_not_a_status"
        broken.pop("schema_version", None)
        return broken
