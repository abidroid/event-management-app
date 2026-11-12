"""HTTP routes for event registrations. Each route delegates to one service function.

Every route requires login: the registrant is always the user in the token.
"""

from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, status

from app.api.deps import UNAUTHORIZED, CurrentUser, EventId, Pagination, SessionDep
from app.models import Registration
from app.schemas.common import ErrorResponse
from app.schemas.registration import RegistrationRead
from app.services import registration_service

router = APIRouter(tags=["registrations"])

EVENT_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Event not found"}
}


@router.post(
    "/events/{event_id}/registrations",
    summary="Register for an event",
    description=(
        "Sign the logged-in user up for an event. No request body is needed. "
        "Fails with 409 if you are already registered or the event is full."
    ),
    response_model=RegistrationRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        **UNAUTHORIZED,
        **EVENT_NOT_FOUND,
        409: {"model": ErrorResponse, "description": "Already registered or full"},
    },
)
async def register_for_event(
    event_id: EventId, session: SessionDep, current_user: CurrentUser
) -> Registration:
    """Register the current user for an event.

    Args:
        event_id: Id of the event.
        session: Database session for this request.
        current_user: The logged-in user, who becomes the registrant.

    Returns:
        The new registration.
    """
    return await registration_service.register_for_event(
        session, event_id, current_user
    )


@router.get(
    "/events/{event_id}/registrations",
    summary="List an event's registrations",
    description=(
        "Return a page of the people registered for an event, oldest sign-up "
        "first, with each person's name and email. Requires login."
    ),
    response_model=list[RegistrationRead],
    status_code=status.HTTP_200_OK,
    responses={**UNAUTHORIZED, **EVENT_NOT_FOUND},
)
async def list_registrations(
    event_id: EventId,
    session: SessionDep,
    pagination: Pagination,
    current_user: CurrentUser,
) -> Sequence[Registration]:
    """List registrations for an event, one page at a time.

    Args:
        event_id: Id of the event.
        session: Database session for this request.
        pagination: Validated skip and limit values.
        current_user: The logged-in user; required so anonymous clients get 401.

    Returns:
        The requested page of registrations.
    """
    return await registration_service.list_registrations(
        session, event_id, pagination.skip, pagination.limit
    )
