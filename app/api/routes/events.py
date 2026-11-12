"""HTTP routes for events. Each route delegates to exactly one service function.

Reading events is public; creating, updating and deleting require a bearer token.
"""

from collections.abc import Sequence
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, EventId, Pagination, SessionDep
from app.api.responses import CAPACITY_CONFLICT, EVENT_NOT_FOUND, UNAUTHORIZED
from app.models import Event
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    summary="Create an event",
    description="Create a new corporate event. Requires login; you become its creator.",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    responses=UNAUTHORIZED,
)
async def create_event(
    data: EventCreate, session: SessionDep, current_user: CurrentUser
) -> Event:
    """Create an event.

    Args:
        data: Validated event fields from the request body.
        session: Database session for this request.
        current_user: The logged-in user, recorded as the event's creator.

    Returns:
        The created event.
    """
    return await event_service.create_event(session, data, current_user.id)


@router.get(
    "",
    summary="List events",
    description=(
        "Return a page of events ordered by date, then id. Use `skip` and `limit` "
        "to page through results, `title` for a case-insensitive partial match and "
        "`date` for an exact day. Filters and paging can be combined."
    ),
    response_model=list[EventRead],
    status_code=status.HTTP_200_OK,
    # No custom `responses=`: FastAPI already documents 422 with its standard
    # validation-error schema, which is the body clients actually receive.
)
async def list_events(
    session: SessionDep,
    pagination: Pagination,
    title: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=200,
            description="Only events whose title contains this text (any case).",
        ),
    ] = None,
    # Aliased so the public name stays `date` without shadowing datetime.date.
    event_date: Annotated[
        date | None,
        Query(alias="date", description="Only events on this day (YYYY-MM-DD)."),
    ] = None,
) -> Sequence[Event]:
    """List events, one page at a time, with optional filters.

    Args:
        session: Database session for this request.
        pagination: Validated skip and limit values.
        title: Optional title search text.
        event_date: Optional exact event day.

    Returns:
        The requested page of matching events in date order.
    """
    return await event_service.list_events(
        session, pagination.skip, pagination.limit, title, event_date
    )


@router.get(
    "/{event_id}",
    summary="Get an event",
    description="Return a single event by id.",
    response_model=EventRead,
    status_code=status.HTTP_200_OK,
    responses=EVENT_NOT_FOUND,
)
async def get_event(event_id: EventId, session: SessionDep) -> Event:
    """Get one event.

    Args:
        event_id: Id of the event.
        session: Database session for this request.

    Returns:
        The requested event.
    """
    return await event_service.get_event(session, event_id)


@router.put(
    "/{event_id}",
    summary="Update an event",
    description=(
        "Change some or all fields of an event. Fields not sent are left unchanged. "
        "Requires login."
    ),
    response_model=EventRead,
    status_code=status.HTTP_200_OK,
    responses={
        **UNAUTHORIZED,
        **EVENT_NOT_FOUND,
        **CAPACITY_CONFLICT,
    },
)
async def update_event(
    event_id: EventId, data: EventUpdate, session: SessionDep, current_user: CurrentUser
) -> Event:
    """Update an event.

    Args:
        event_id: Id of the event.
        data: Fields to change.
        session: Database session for this request.
        current_user: The logged-in user; required so anonymous clients get 401.

    Returns:
        The updated event.
    """
    return await event_service.update_event(session, event_id, data)


@router.delete(
    "/{event_id}",
    summary="Delete an event",
    description="Permanently delete an event. Requires login.",
    # 204 responses never have a body, so there is no schema to document.
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**UNAUTHORIZED, **EVENT_NOT_FOUND},
)
async def delete_event(
    event_id: EventId, session: SessionDep, current_user: CurrentUser
) -> None:
    """Delete an event.

    Args:
        event_id: Id of the event.
        session: Database session for this request.
        current_user: The logged-in user; required so anonymous clients get 401.
    """
    await event_service.delete_event(session, event_id)
