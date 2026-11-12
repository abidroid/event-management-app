"""Business logic for creating, reading, updating and deleting events."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EventNotFoundError
from app.models import Event
from app.schemas.event import EventCreate, EventUpdate


async def _get_event_or_raise(session: AsyncSession, event_id: int) -> Event:
    """Load an event by id, shared by every function that needs an existing event.

    Args:
        session: Active database session.
        event_id: Primary key of the event.

    Returns:
        The matching `Event`.

    Raises:
        EventNotFoundError: If no event has this id.
    """
    event = await session.get(Event, event_id)
    if event is None:
        raise EventNotFoundError(event_id)
    return event


async def create_event(
    session: AsyncSession, data: EventCreate, created_by: int
) -> Event:
    """Insert a new event owned by the user who created it.

    Args:
        session: Active database session.
        data: Validated event fields.
        created_by: Id of the logged-in user creating the event.

    Returns:
        The saved `Event`, including database-generated id and timestamps.
    """
    event = Event(**data.model_dump(), created_by=created_by)
    session.add(event)
    await session.commit()
    # Reload so server-generated columns (created_at, updated_at) are populated.
    await session.refresh(event)
    return event


async def list_events(session: AsyncSession) -> Sequence[Event]:
    """Return all events in a stable order.

    Args:
        session: Active database session.

    Returns:
        Events ordered by date, then id (so events on the same day never swap places).
    """
    result = await session.execute(select(Event).order_by(Event.event_date, Event.id))
    return result.scalars().all()


async def get_event(session: AsyncSession, event_id: int) -> Event:
    """Return one event.

    Args:
        session: Active database session.
        event_id: Primary key of the event.

    Returns:
        The matching `Event`.

    Raises:
        EventNotFoundError: If no event has this id.
    """
    return await _get_event_or_raise(session, event_id)


async def update_event(
    session: AsyncSession, event_id: int, data: EventUpdate
) -> Event:
    """Apply a partial update to an event.

    Args:
        session: Active database session.
        event_id: Primary key of the event.
        data: Fields to change; fields the client did not send are left alone.

    Returns:
        The updated `Event`.

    Raises:
        EventNotFoundError: If no event has this id.
    """
    event = await _get_event_or_raise(session, event_id)
    # exclude_unset distinguishes "not sent" from "sent as null", so a client
    # can update one field without wiping the others.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    await session.commit()
    await session.refresh(event)
    return event


async def delete_event(session: AsyncSession, event_id: int) -> None:
    """Delete an event.

    Args:
        session: Active database session.
        event_id: Primary key of the event.

    Raises:
        EventNotFoundError: If no event has this id.
    """
    event = await _get_event_or_raise(session, event_id)
    await session.delete(event)
    await session.commit()
