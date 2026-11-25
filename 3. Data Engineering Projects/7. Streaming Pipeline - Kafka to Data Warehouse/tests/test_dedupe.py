from src.loader.rules import latest_per_key


def test_keeps_the_newest_event_per_key() -> None:
    rows = [
        {"order_id": "ord_1", "event_time": "2024-01-01T10:00:00Z", "status": "created"},
        {"order_id": "ord_1", "event_time": "2024-01-01T12:00:00Z", "status": "paid"},
        {"order_id": "ord_2", "event_time": "2024-01-01T11:00:00Z", "status": "created"},
    ]
    result = {row["order_id"]: row for row in latest_per_key(rows)}
    assert result["ord_1"]["status"] == "paid"
    assert result["ord_2"]["status"] == "created"
    assert len(result) == 2


def test_older_event_never_wins() -> None:
    rows = [
        {"order_id": "ord_1", "event_time": "2024-01-01T12:00:00Z", "status": "shipped"},
        {"order_id": "ord_1", "event_time": "2024-01-01T10:00:00Z", "status": "created"},
    ]
    assert latest_per_key(rows)[0]["status"] == "shipped"


def test_output_is_deterministically_ordered() -> None:
    rows = [
        {"order_id": "ord_b", "event_time": "2024-01-01T10:00:00Z"},
        {"order_id": "ord_a", "event_time": "2024-01-01T10:00:00Z"},
    ]
    assert [row["order_id"] for row in latest_per_key(rows)] == ["ord_a", "ord_b"]


def test_empty_input() -> None:
    assert latest_per_key([]) == []


def test_falls_back_when_timestamp_is_missing() -> None:
    rows = [
        {"order_id": "ord_1", "event_time": None, "status": "created"},
        {"order_id": "ord_1", "event_time": "2024-01-01T10:00:00Z", "status": "paid"},
    ]
    assert latest_per_key(rows)[0]["status"] == "paid"
