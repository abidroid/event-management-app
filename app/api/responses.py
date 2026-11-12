"""OpenAPI documentation for the error responses that routes can return.

These dicts are passed to a route's `responses=` argument. They only affect the
generated docs (/docs and /openapi.json); the real error bodies come from the
domain exception handler in app/main.py.
"""

from typing import Any

from app.schemas.common import ErrorResponse

# The type FastAPI expects for a route's `responses=` argument.
Responses = dict[int | str, dict[str, Any]]


def error_response(description: str, detail: str) -> dict[str, Any]:
    """Describe one error status code for OpenAPI.

    The ErrorResponse schema has a single generic example, so each status code
    gets its own example here; otherwise Swagger shows "Event 42 not found"
    under 401, 403 and 409 too.

    Args:
        description: Short explanation shown next to the status code.
        detail: An example `detail` message the client would receive.

    Returns:
        A `responses=` entry with the ErrorResponse model and a matching example.
    """
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {"application/json": {"example": {"detail": detail}}},
    }


UNAUTHORIZED: Responses = {
    401: error_response(
        "Missing, invalid or expired token", "Could not validate credentials"
    )
}

BAD_LOGIN: Responses = {
    401: error_response("Incorrect email or password", "Incorrect email or password")
}

EMAIL_TAKEN: Responses = {
    409: error_response(
        "Email already registered", "Email ada.lovelace@acme.com is already registered"
    )
}

EVENT_NOT_FOUND: Responses = {
    404: error_response("Event not found", "Event 42 not found")
}

CAPACITY_CONFLICT: Responses = {
    409: error_response(
        "New capacity is below the current registrations",
        "Capacity 5 is below the 12 people already registered",
    )
}

REGISTRATION_CONFLICT: Responses = {
    409: error_response(
        "Already registered for this event, or the event is full",
        "Event 42 is full",
    )
}

REGISTRATION_NOT_FOUND: Responses = {
    404: error_response("Registration not found", "Registration 7 not found")
}

NOT_OWNER: Responses = {
    403: error_response(
        "Not your registration", "You can only cancel your own registrations"
    )
}
