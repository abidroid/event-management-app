"""ORM model for the `registrations` table."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    # Imported only for type hints: event.py imports this module at runtime,
    # so a runtime import here would be circular.
    from app.models.event import Event
    from app.models.user import User


class Registration(Base):
    """One user's seat at one event.

    Attributes:
        id: Primary key.
        event_id: Id of the event; the row is deleted with its event.
        user_id: Id of the registered user.
        registered_at: When the user signed up (set by the database).
        event: The event this registration belongs to.
        user: The registered user.
    """

    __tablename__ = "registrations"
    # A safety net behind the service's duplicate check: even if two requests
    # slipped past it, the database refuses a second row for the same pair.
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_registrations_event_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE", name="fk_registrations_event_id")
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_registrations_user_id"), index=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    event: Mapped["Event"] = relationship(back_populates="registrations")
    # Joined loading fetches the user in the same query as the registration.
    # Async sessions cannot lazy-load later, and every response shows the
    # registrant's name and email, so the user is always needed.
    user: Mapped["User"] = relationship(lazy="joined")
