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
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


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
