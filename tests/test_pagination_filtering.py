"""Tests for pagination (skip/limit) and filters (title/date) on GET /events."""

from datetime import date, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


async def create_events(
    client: AsyncClient,
    headers: dict[str, str],
    base: dict[str, Any],
    events: list[tuple[str, int]],
) -> None:
    """Create several events through the API.

    Args:
        client: The test HTTP client.
        headers: Auth headers for a logged-in user.
        base: A valid event body used for every other field.
        events: (title, days from today) pairs, created in this order.
    """
    for title, days_ahead in events:
        body = {
            **base,
            "title": title,
            "event_date": (date.today() + timedelta(days=days_ahead)).isoformat(),
        }
        response = await client.post("/events", json=body, headers=headers)
        assert response.status_code == 201


def titles(response_json: list[dict[str, Any]]) -> list[str]:
    """Extract event titles from a GET /events response body.

    Args:
        response_json: The decoded JSON list of events.

    Returns:
        The titles in response order.
    """
    return [event["title"] for event in response_json]


# --- Pagination ---------------------------------------------------------------


async def test_default_limit_is_10(
    client: AsyncClient, event_payload: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """Without skip/limit, GET /events returns the first 10 events."""
    await create_events(
        client, auth_headers, event_payload, [(f"Event {i}", i) for i in range(1, 13)]
    )

    response = await client.get("/events")

    assert response.status_code == 200
    assert titles(response.json()) == [f"Event {i}" for i in range(1, 11)]


async def test_skip_and_limit_return_the_requested_slice(
    client: AsyncClient, event_payload: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """skip and limit select a window of the date-ordered list."""
    await create_events(
        client, auth_headers, event_payload, [(f"Event {i}", i) for i in range(1, 6)]
    )

    response = await client.get("/events", params={"skip": 1, "limit": 2})

    assert response.status_code == 200
    assert titles(response.json()) == ["Event 2", "Event 3"]


async def test_pages_are_stable_for_events_on_the_same_day(
    client: AsyncClient, event_payload: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """Same-day events are ordered by id, so consecutive pages never overlap."""
    await create_events(
        client, auth_headers, event_payload, [(f"Same day {i}", 7) for i in range(4)]
    )

    first = await client.get("/events", params={"skip": 0, "limit": 2})
    second = await client.get("/events", params={"skip": 2, "limit": 2})

    assert titles(first.json()) == ["Same day 0", "Same day 1"]
    assert titles(second.json()) == ["Same day 2", "Same day 3"]


async def test_skip_past_the_end_returns_empty_list(
    client: AsyncClient, event: dict[str, Any]
) -> None:
    """Skipping more events than exist gives an empty page, not an error."""
    response = await client.get("/events", params={"skip": 50})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("limit", [1, 100])
async def test_limit_boundaries_are_accepted(
    client: AsyncClient, event: dict[str, Any], limit: int
) -> None:
    """The smallest and largest allowed limits are valid."""
    response = await client.get("/events", params={"limit": limit})

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.parametrize(
    "params",
    [
        {"skip": -1},
        {"limit": 0},
        {"limit": 101},
        {"limit": "abc"},
        {"skip": "abc"},
    ],
)
async def test_out_of_range_pagination_returns_422(
    client: AsyncClient, params: dict[str, Any]
) -> None:
    """skip below 0 or limit outside 1-100 is rejected by validation."""
    response = await client.get("/events", params=params)

    assert response.status_code == 422


# --- Filters ------------------------------------------------------------------


@pytest.mark.parametrize("search", ["town", "TOWN HALL", "Quarterly"])
async def test_title_filter_is_case_insensitive_partial_match(
    client: AsyncClient,
    event_payload: dict[str, Any],
    auth_headers: dict[str, str],
    search: str,
) -> None:
    """title matches any part of the event title, ignoring case."""
    await create_events(
        client,
        auth_headers,
        event_payload,
        [("Quarterly Town Hall", 5), ("Team Offsite", 6)],
    )

    response = await client.get("/events", params={"title": search})

    assert response.status_code == 200
    assert titles(response.json()) == ["Quarterly Town Hall"]


async def test_title_filter_with_no_match_returns_empty_list(
    client: AsyncClient, event: dict[str, Any]
) -> None:
    """A title that matches nothing gives an empty list."""
    response = await client.get("/events", params={"title": "Hackathon"})

    assert response.status_code == 200
    assert response.json() == []


async def test_empty_title_filter_returns_422(client: AsyncClient) -> None:
    """An empty title search is rejected rather than silently matching everything."""
    response = await client.get("/events", params={"title": ""})

    assert response.status_code == 422


async def test_date_filter_is_exact_match(
    client: AsyncClient, event_payload: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """date returns only events on exactly that day."""
    await create_events(
        client,
        auth_headers,
        event_payload,
        [("Before", 9), ("On the day", 10), ("Also on the day", 10), ("After", 11)],
    )
    target = (date.today() + timedelta(days=10)).isoformat()

    response = await client.get("/events", params={"date": target})

    assert response.status_code == 200
    assert titles(response.json()) == ["On the day", "Also on the day"]


@pytest.mark.parametrize("bad_date", ["2026-13-45", "tomorrow", "15/12/2026"])
async def test_invalid_date_filter_returns_422(
    client: AsyncClient, bad_date: str
) -> None:
    """A date that is not a valid YYYY-MM-DD day is rejected."""
    response = await client.get("/events", params={"date": bad_date})

    assert response.status_code == 422


# --- Combinations -------------------------------------------------------------


async def test_title_and_date_filters_combine(
    client: AsyncClient, event_payload: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """Both filters apply together: an event must match title AND date."""
    await create_events(
        client,
        auth_headers,
        event_payload,
        [("Town Hall", 10), ("Town Hall", 20), ("Offsite", 10)],
    )
    target = (date.today() + timedelta(days=10)).isoformat()

    response = await client.get("/events", params={"title": "town", "date": target})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Town Hall"
    assert body[0]["event_date"] == target


async def test_filters_combine_with_pagination(
    client: AsyncClient, event_payload: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """Paging is applied to the filtered results, not to the whole table."""
    await create_events(
        client,
        auth_headers,
        event_payload,
        [
            ("Workshop 1", 1),
            ("Lunch", 2),
            ("Workshop 2", 3),
            ("Lunch", 4),
            ("Workshop 3", 5),
        ],
    )

    response = await client.get(
        "/events", params={"title": "workshop", "skip": 1, "limit": 1}
    )

    assert response.status_code == 200
    assert titles(response.json()) == ["Workshop 2"]
