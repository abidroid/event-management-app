"""Tests for request-body validation on the /events endpoints (422 cases)."""

from datetime import date, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", ""),
        ("title", "   "),
        ("title", "x" * 201),
        ("description", "x" * 2001),
        ("location", ""),
        ("location", "x" * 201),
        ("max_capacity", 0),
        ("max_capacity", -1),
        ("max_capacity", 10001),
        ("max_capacity", "abc"),
        ("event_date", str(date.today() - timedelta(days=1))),
        ("event_date", "not-a-date"),
    ],
)
async def test_create_event_invalid_field_returns_422(
    client: AsyncClient, event_payload: dict[str, Any], field: str, value: Any
) -> None:
    """POST /events rejects each invalid field value with 422."""
    event_payload[field] = value

    response = await client.post("/events", json=event_payload)

    assert response.status_code == 422
    # FastAPI reports the failing field's location, e.g. ["body", "title"].
    assert response.json()["detail"][0]["loc"][-1] == field


async def test_create_event_strips_title_whitespace(
    client: AsyncClient, event_payload: dict[str, Any]
) -> None:
    """Surrounding whitespace in the title is trimmed before saving."""
    event_payload["title"] = "  Town Hall  "

    response = await client.post("/events", json=event_payload)

    assert response.status_code == 201
    assert response.json()["title"] == "Town Hall"


async def test_create_event_dated_today_returns_201(
    client: AsyncClient, event_payload: dict[str, Any]
) -> None:
    """An event dated today is not in the past, so it is accepted."""
    event_payload["event_date"] = str(date.today())

    response = await client.post("/events", json=event_payload)

    assert response.status_code == 201


async def test_create_event_at_max_capacity_limit_returns_201(
    client: AsyncClient, event_payload: dict[str, Any]
) -> None:
    """The upper capacity bound (10000) is inclusive."""
    event_payload["max_capacity"] = 10000

    response = await client.post("/events", json=event_payload)

    assert response.status_code == 201


@pytest.mark.parametrize(
    "body",
    [{"max_capacity": 0}, {"title": "   "}, {"title": None}, {"location": None}],
)
async def test_update_event_invalid_body_returns_422(
    client: AsyncClient, event: dict[str, Any], body: dict[str, Any]
) -> None:
    """PUT /events/{id} applies the same rules and rejects null for required fields."""
    response = await client.put(f"/events/{event['id']}", json=body)

    assert response.status_code == 422


async def test_update_event_can_clear_description(
    client: AsyncClient, event: dict[str, Any]
) -> None:
    """Description is optional, so sending null clears it."""
    response = await client.put(f"/events/{event['id']}", json={"description": None})

    assert response.status_code == 200
    assert response.json()["description"] is None
