"""Tests for the /events CRUD endpoints."""

from datetime import date, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


async def test_create_event_returns_201(
    client: AsyncClient, event_payload: dict[str, Any]
) -> None:
    """POST /events stores the event and returns it with an id and timestamps."""
    response = await client.post("/events", json=event_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == event_payload["title"]
    assert body["event_date"] == event_payload["event_date"]
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


async def test_create_event_missing_field_returns_422(
    client: AsyncClient, event_payload: dict[str, Any]
) -> None:
    """POST /events without a required field is rejected by validation."""
    del event_payload["title"]

    response = await client.post("/events", json=event_payload)

    assert response.status_code == 422


async def test_list_events_empty(client: AsyncClient) -> None:
    """GET /events returns an empty list when there are no events."""
    response = await client.get("/events")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_events_ordered_by_date(
    client: AsyncClient, event_payload: dict[str, Any]
) -> None:
    """GET /events returns events ordered by date, earliest first."""
    later = {
        **event_payload,
        "title": "Later",
        "event_date": str(date.today() + timedelta(days=60)),
    }
    sooner = {
        **event_payload,
        "title": "Sooner",
        "event_date": str(date.today() + timedelta(days=5)),
    }
    await client.post("/events", json=later)
    await client.post("/events", json=sooner)

    response = await client.get("/events")

    assert response.status_code == 200
    assert [e["title"] for e in response.json()] == ["Sooner", "Later"]


async def test_get_event_returns_200(
    client: AsyncClient, event: dict[str, Any]
) -> None:
    """GET /events/{id} returns the matching event."""
    response = await client.get(f"/events/{event['id']}")

    assert response.status_code == 200
    assert response.json() == event


async def test_update_event_changes_only_sent_fields(
    client: AsyncClient, event: dict[str, Any]
) -> None:
    """PUT /events/{id} with a partial body leaves the other fields unchanged."""
    response = await client.put(f"/events/{event['id']}", json={"location": "Room B"})

    assert response.status_code == 200
    body = response.json()
    assert body["location"] == "Room B"
    assert body["title"] == event["title"]
    assert body["max_capacity"] == event["max_capacity"]


async def test_delete_event_returns_204_and_removes_it(
    client: AsyncClient, event: dict[str, Any]
) -> None:
    """DELETE /events/{id} removes the event, so a later GET returns 404."""
    response = await client.delete(f"/events/{event['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert (await client.get(f"/events/{event['id']}")).status_code == 404


@pytest.mark.parametrize(
    ("method", "body"),
    [("GET", None), ("PUT", {"location": "Room B"}), ("DELETE", None)],
)
async def test_unknown_event_returns_404(
    client: AsyncClient, method: str, body: dict[str, Any] | None
) -> None:
    """GET, PUT and DELETE on a missing event return 404 with a detail message."""
    response = await client.request(method, "/events/999", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": "Event 999 not found"}


@pytest.mark.parametrize("bad_id", ["0", "-1", "abc"])
async def test_invalid_event_id_returns_422(client: AsyncClient, bad_id: str) -> None:
    """A non-positive or non-integer event id is rejected before any lookup."""
    response = await client.get(f"/events/{bad_id}")

    assert response.status_code == 422
