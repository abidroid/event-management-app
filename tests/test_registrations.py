"""Tests for registering for events, listing registrations and cancelling them."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from httpx import AsyncClient

# The factory fixture from conftest.py: (email, full_name) -> auth headers.
MakeAuthHeaders = Callable[[str, str], Awaitable[dict[str, str]]]


async def _create_event(
    client: AsyncClient,
    event_payload: dict[str, Any],
    headers: dict[str, str],
    max_capacity: int,
) -> int:
    """Create an event with a given capacity and return its id.

    Args:
        client: The test HTTP client.
        event_payload: A valid event body to start from.
        headers: Headers for a logged-in user.
        max_capacity: Number of seats the event should have.

    Returns:
        The new event's id.
    """
    body = {**event_payload, "max_capacity": max_capacity}
    response = await client.post("/events", json=body, headers=headers)
    assert response.status_code == 201
    return int(response.json()["id"])


# --- POST /events/{id}/registrations --------------------------------------


async def test_register_returns_201_with_user_details(
    client: AsyncClient,
    event: dict[str, Any],
    auth_headers: dict[str, str],
    user_payload: dict[str, str],
) -> None:
    """Registering returns the registration with the user's name and email."""
    response = await client.post(
        f"/events/{event['id']}/registrations", headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["event_id"] == event["id"]
    assert body["registered_at"] is not None
    assert body["user"] == {
        "full_name": user_payload["full_name"],
        "email": user_payload["email"],
    }


async def test_register_without_token_returns_401(
    client: AsyncClient, event: dict[str, Any]
) -> None:
    """Registering requires login."""
    response = await client.post(f"/events/{event['id']}/registrations")

    assert response.status_code == 401


async def test_register_unknown_event_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """Registering for an event that does not exist gives 404."""
    response = await client.post("/events/999/registrations", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Event 999 not found"}


async def test_register_non_positive_event_id_returns_422(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """A non-positive event id is rejected before any database work."""
    response = await client.post("/events/0/registrations", headers=auth_headers)

    assert response.status_code == 422


async def test_register_twice_returns_409(
    client: AsyncClient, event: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """The same user cannot register for the same event twice."""
    url = f"/events/{event['id']}/registrations"
    await client.post(url, headers=auth_headers)

    response = await client.post(url, headers=auth_headers)

    assert response.status_code == 409
    assert response.json() == {
        "detail": f"You are already registered for event {event['id']}"
    }


async def test_register_for_full_event_returns_409(
    client: AsyncClient,
    event_payload: dict[str, Any],
    auth_headers: dict[str, str],
    make_auth_headers: MakeAuthHeaders,
) -> None:
    """Once every seat is taken, the next user is turned away."""
    event_id = await _create_event(client, event_payload, auth_headers, max_capacity=2)
    url = f"/events/{event_id}/registrations"
    for number in (1, 2):
        headers = await make_auth_headers(f"user{number}@acme.com", f"User {number}")
        assert (await client.post(url, headers=headers)).status_code == 201

    response = await client.post(url, headers=auth_headers)

    assert response.status_code == 409
    assert response.json() == {"detail": f"Event {event_id} is full"}


async def test_simultaneous_registrations_cannot_overfill_event(
    client: AsyncClient,
    event_payload: dict[str, Any],
    auth_headers: dict[str, str],
    make_auth_headers: MakeAuthHeaders,
) -> None:
    """Two sign-ups racing for the last seat: the row lock lets only one win."""
    event_id = await _create_event(client, event_payload, auth_headers, max_capacity=1)
    url = f"/events/{event_id}/registrations"
    first = await make_auth_headers("first@acme.com", "First User")
    second = await make_auth_headers("second@acme.com", "Second User")

    responses = await asyncio.gather(
        client.post(url, headers=first), client.post(url, headers=second)
    )

    assert sorted(r.status_code for r in responses) == [201, 409]
    event = (await client.get(f"/events/{event_id}")).json()
    assert event["registered_count"] == 1


async def test_registering_updates_seat_counts(
    client: AsyncClient, event: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """The event shows one more registration and one fewer seat."""
    await client.post(f"/events/{event['id']}/registrations", headers=auth_headers)

    body = (await client.get(f"/events/{event['id']}")).json()

    assert body["registered_count"] == 1
    assert body["seats_left"] == event["max_capacity"] - 1


# --- GET /events/{id}/registrations ----------------------------------------


async def test_list_registrations_returns_names_and_emails(
    client: AsyncClient,
    event: dict[str, Any],
    auth_headers: dict[str, str],
    make_auth_headers: MakeAuthHeaders,
) -> None:
    """The list shows every registrant, oldest sign-up first."""
    url = f"/events/{event['id']}/registrations"
    await client.post(url, headers=auth_headers)
    other = await make_auth_headers("grace.hopper@acme.com", "Grace Hopper")
    await client.post(url, headers=other)

    response = await client.get(url, headers=auth_headers)

    assert response.status_code == 200
    names = [item["user"]["full_name"] for item in response.json()]
    assert names == ["Ada Lovelace", "Grace Hopper"]


async def test_list_registrations_is_paginated(
    client: AsyncClient,
    event: dict[str, Any],
    auth_headers: dict[str, str],
    make_auth_headers: MakeAuthHeaders,
) -> None:
    """skip and limit select one page of registrations."""
    url = f"/events/{event['id']}/registrations"
    await client.post(url, headers=auth_headers)
    other = await make_auth_headers("grace.hopper@acme.com", "Grace Hopper")
    await client.post(url, headers=other)

    response = await client.get(
        url, params={"skip": 1, "limit": 1}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["user"]["full_name"] == "Grace Hopper"


async def test_list_registrations_unknown_event_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """Listing registrations of a missing event gives 404, not an empty list."""
    response = await client.get("/events/999/registrations", headers=auth_headers)

    assert response.status_code == 404


async def test_list_registrations_without_token_returns_401(
    client: AsyncClient, event: dict[str, Any]
) -> None:
    """Registrant names and emails are only visible to logged-in users."""
    response = await client.get(f"/events/{event['id']}/registrations")

    assert response.status_code == 401


async def test_list_registrations_bad_limit_returns_422(
    client: AsyncClient, event: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """limit must be between 1 and 100."""
    response = await client.get(
        f"/events/{event['id']}/registrations",
        params={"limit": 0},
        headers=auth_headers,
    )

    assert response.status_code == 422


# --- DELETE /registrations/{id} --------------------------------------------


async def test_cancel_registration_returns_204_and_frees_seat(
    client: AsyncClient,
    event_payload: dict[str, Any],
    auth_headers: dict[str, str],
    make_auth_headers: MakeAuthHeaders,
) -> None:
    """Cancelling frees the seat, so another user can take it."""
    event_id = await _create_event(client, event_payload, auth_headers, max_capacity=1)
    url = f"/events/{event_id}/registrations"
    registration = (await client.post(url, headers=auth_headers)).json()

    response = await client.delete(
        f"/registrations/{registration['id']}", headers=auth_headers
    )

    assert response.status_code == 204
    other = await make_auth_headers("grace.hopper@acme.com", "Grace Hopper")
    assert (await client.post(url, headers=other)).status_code == 201


async def test_cancel_someone_elses_registration_returns_403(
    client: AsyncClient,
    event: dict[str, Any],
    auth_headers: dict[str, str],
    make_auth_headers: MakeAuthHeaders,
) -> None:
    """A user cannot cancel another user's registration."""
    registration = (
        await client.post(f"/events/{event['id']}/registrations", headers=auth_headers)
    ).json()
    intruder = await make_auth_headers("mallory@acme.com", "Mallory")

    response = await client.delete(
        f"/registrations/{registration['id']}", headers=intruder
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You can only cancel your own registrations"}


async def test_cancel_unknown_registration_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """Cancelling a registration that does not exist gives 404."""
    response = await client.delete("/registrations/999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Registration 999 not found"}


async def test_cancel_registration_without_token_returns_401(
    client: AsyncClient,
) -> None:
    """Cancelling requires login."""
    response = await client.delete("/registrations/1")

    assert response.status_code == 401


async def test_deleting_event_removes_its_registrations(
    client: AsyncClient, event: dict[str, Any], auth_headers: dict[str, str]
) -> None:
    """Registrations are deleted together with their event (ON DELETE CASCADE)."""
    registration = (
        await client.post(f"/events/{event['id']}/registrations", headers=auth_headers)
    ).json()

    response = await client.delete(f"/events/{event['id']}", headers=auth_headers)

    assert response.status_code == 204
    response = await client.delete(
        f"/registrations/{registration['id']}", headers=auth_headers
    )
    assert response.status_code == 404
