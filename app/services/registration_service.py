"""Business logic for signing up for events, listing sign-ups and cancelling them."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateRegistrationError,
    EventFullError,
    EventNotFoundError,
)
from app.models import Event, Registration, User
from app.services import event_service


async def _count_registrations(session: AsyncSession, event_id: int) -> int:
    """Count how many people are registered for an event.

    Args:
        session: Active database session.
        event_id: Primary key of the event.

    Returns:
        The number of registrations for the event.
    """
    count = await session.scalar(
        select(func.count(Registration.id)).where(Registration.event_id == event_id)
    )
    # count() always returns a row, but scalar() is typed as optional.
    return count or 0


async def register_for_event(
    session: AsyncSession, event_id: int, user: User
) -> Registration:
    """Register the logged-in user for an event, if a seat is free.

    Rules are checked in this order: the event exists, the user is not
    already registered, and the event still has a free seat.

    Args:
        session: Active database session.
        event_id: Primary key of the event.
        user: The logged-in user signing up.

    Returns:
        The saved `Registration`, including the registrant's name and email.

    Raises:
        EventNotFoundError: If no event has this id.
        DuplicateRegistrationError: If the user is already registered.
        EventFullError: If every seat is taken.
    """
    # SELECT ... FOR UPDATE locks the event row until this transaction commits.
    # A second sign-up for the same event waits here, so two people can never
    # both see "one seat left" and both take it.
    event = await session.scalar(
        select(Event).where(Event.id == event_id).with_for_update()
    )
    if event is None:
        raise EventNotFoundError(event_id)

    already_registered = await session.scalar(
        select(Registration.id).where(
            Registration.event_id == event_id, Registration.user_id == user.id
        )
    )
    if already_registered is not None:
        raise DuplicateRegistrationError(event_id)

    # Counted in a fresh query after taking the lock, so the count includes
    # any sign-up that committed while this request was waiting.
    if await _count_registrations(session, event_id) >= event.max_capacity:
        raise EventFullError(event_id)

    registration = Registration(event_id=event_id, user_id=user.id, user=user)
    session.add(registration)
    await session.commit()
    # Reload so the database-generated registered_at is populated.
    await session.refresh(registration)
    return registration


async def list_registrations(
    session: AsyncSession, event_id: int, skip: int, limit: int
) -> Sequence[Registration]:
    """Return one page of an event's registrations, oldest first.

    Args:
        session: Active database session.
        event_id: Primary key of the event.
        skip: Number of registrations to skip.
        limit: Maximum number of registrations to return.

    Returns:
        The registrations, each with the registrant's name and email.

    Raises:
        EventNotFoundError: If no event has this id.
    """
    # Without this check an unknown event would return an empty list, which
    # looks the same as "nobody registered yet".
    await event_service.get_event(session, event_id)
    result = await session.execute(
        select(Registration)
        .where(Registration.event_id == event_id)
        # id breaks ties so pages stay stable.
        .order_by(Registration.registered_at, Registration.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
