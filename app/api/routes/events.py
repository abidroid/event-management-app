"""HTTP routes for events. Each route delegates to exactly one service function."""

from collections.abc import Sequence
from typing import Annotated, Any

from fastapi import APIRouter, Path, status

from app.api.deps import SessionDep
from app.models import Event
from app.schemas.common import ErrorResponse
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])

# Shared path parameter: non-positive ids are rejected with 422 before any query.
EventId = Annotated[int, Path(gt=0, description="Id of the event.")]

NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Event not found"}
}


@router.post(
    "",
    summary="Create an event",
    description="Create a new corporate event.",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(data: EventCreate, session: SessionDep) -> Event:
    """Create an event.

    Args:
        data: Validated event fields from the request body.
        session: Database session for this request.

    Returns:
        The created event.
    """
    return await event_service.create_event(session, data)


@router.get(
    "",
    summary="List events",
    description="Return all events ordered by date, then id.",
    response_model=list[EventRead],
    status_code=status.HTTP_200_OK,
)
async def list_events(session: SessionDep) -> Sequence[Event]:
    """List events.

    Args:
        session: Database session for this request.

    Returns:
        All events in date order.
    """
    return await event_service.list_events(session)


@router.get(
    "/{event_id}",
    summary="Get an event",
    description="Return a single event by id.",
    response_model=EventRead,
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND,
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
    description="Change some or all fields of an event. Fields not sent are left unchanged.",
    response_model=EventRead,
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND,
)
async def update_event(
    event_id: EventId, data: EventUpdate, session: SessionDep
) -> Event:
    """Update an event.

    Args:
        event_id: Id of the event.
        data: Fields to change.
        session: Database session for this request.

    Returns:
        The updated event.
    """
    return await event_service.update_event(session, event_id, data)


@router.delete(
    "/{event_id}",
    summary="Delete an event",
    description="Permanently delete an event.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
async def delete_event(event_id: EventId, session: SessionDep) -> None:
    """Delete an event.

    Args:
        event_id: Id of the event.
        session: Database session for this request.
    """
    await event_service.delete_event(session, event_id)
