"""Tests that every domain exception maps to the right HTTP status and body.

The 409 exceptions are only raised by registration logic (Phase 6), so here
the shared handler is called directly; end-to-end 409 tests come with that phase.
"""

import json

import pytest
from fastapi import Request

from app.core.exceptions import (
    CapacityBelowRegistrationsError,
    DomainError,
    DuplicateRegistrationError,
    EventFullError,
    EventNotFoundError,
    RegistrationNotFoundError,
)
from app.main import domain_error_handler


@pytest.mark.parametrize(
    ("exc", "status_code", "detail"),
    [
        (EventNotFoundError(7), 404, "Event 7 not found"),
        (RegistrationNotFoundError(3), 404, "Registration 3 not found"),
        (
            DuplicateRegistrationError(7),
            409,
            "You are already registered for event 7",
        ),
        (EventFullError(7), 409, "Event 7 is full"),
        (
            CapacityBelowRegistrationsError(5, 8),
            409,
            "Capacity 5 is below the 8 people already registered",
        ),
    ],
)
async def test_domain_error_handler_maps_status_and_detail(
    exc: DomainError, status_code: int, detail: str
) -> None:
    """The handler returns the exception's status code and {"detail": message}."""
    # The handler ignores the request, so a minimal ASGI scope is enough.
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

    response = await domain_error_handler(request, exc)

    assert response.status_code == status_code
    assert json.loads(bytes(response.body)) == {"detail": detail}
