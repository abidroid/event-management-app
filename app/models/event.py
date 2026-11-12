"""ORM model for the `events` table."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    select,
)
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.db import Base
from app.models.registration import Registration


class Event(Base):
    """A corporate event that employees can register for.

    Attributes:
        id: Primary key.
        title: Short name of the event.
        description: Optional longer text about the event.
        event_date: Calendar day the event takes place.
        location: Where the event is held.
        max_capacity: Maximum number of attendees; must be positive.
        created_by: Id of the user who created the event.
        created_at: When the row was inserted (set by the database).
        updated_at: When the row was last changed (set by the database).
        registrations: Sign-ups for this event; deleted together with it.
        registered_count: How many people are registered (computed, not stored).
    """

    __tablename__ = "events"
    # Enforced in the database as well as in the schemas, so no code path
    # (scripts, migrations, future endpoints) can store an impossible capacity.
    __table_args__ = (
        CheckConstraint("max_capacity > 0", name="ck_events_max_capacity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    event_date: Mapped[date] = mapped_column(Date, index=True)
    location: Mapped[str] = mapped_column(String(200))
    max_capacity: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_events_created_by_users"), index=True
    )
    # Timestamps come from the database clock so every row uses one time source.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # passive_deletes leaves removing the registrations to the database's
    # ON DELETE CASCADE. Without it SQLAlchemy would first load the collection
    # to delete each row itself, and lazy loading is not possible in async code.
    registrations: Mapped[list[Registration]] = relationship(
        back_populates="event", cascade="all, delete-orphan", passive_deletes=True
    )

    # Computed as a subquery inside every SELECT that loads an event, so get,
    # list and refresh all return an up-to-date count in one round trip and the
    # number can never drift out of sync the way a stored counter could.
    registered_count: Mapped[int] = column_property(
        select(func.count(Registration.id))
        .where(Registration.event_id == id)
        .correlate_except(Registration)
        .scalar_subquery()
    )
