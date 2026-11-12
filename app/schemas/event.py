"""Request and response schemas for events, including all input validation."""

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

# Shared field types, declared once so EventCreate and EventUpdate cannot drift
# apart. Whitespace is stripped before the length check, so "   " is rejected.
Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Location = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
Capacity = Annotated[int, Field(gt=0, le=10000)]


class EventCreate(BaseModel):
    """Body for creating an event.

    Attributes:
        title: Short name of the event (1-200 characters after trimming).
        description: Optional longer text about the event (up to 2000 characters).
        event_date: Calendar day the event takes place; today or later.
        location: Where the event is held (1-200 characters after trimming).
        max_capacity: Maximum number of attendees (1-10000).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Quarterly Town Hall",
                "description": "Company-wide update from the leadership team.",
                "event_date": "2026-12-15",
                "location": "Main Auditorium",
                "max_capacity": 200,
            }
        }
    )

    title: Title
    description: Description | None = None
    event_date: date
    location: Location
    max_capacity: Capacity

    @field_validator("event_date")
    @classmethod
    def event_date_not_in_past(cls, value: date) -> date:
        """Reject event dates before today.

        Args:
            value: The parsed event date.

        Returns:
            The date unchanged when it is today or later.

        Raises:
            ValueError: If the date is in the past (Pydantic turns this into a 422).
        """
        if value < date.today():
            raise ValueError("event_date cannot be in the past")
        return value


class EventUpdate(BaseModel):
    """Body for updating an event; only the fields sent are changed.

    Attributes:
        title: New title, if changing it.
        description: New description, if changing it; null clears it.
        event_date: New date, if changing it.
        location: New location, if changing it.
        max_capacity: New capacity, if changing it.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"location": "Conference Room B", "max_capacity": 50}
        }
    )

    title: Title | None = None
    description: Description | None = None
    event_date: date | None = None
    location: Location | None = None
    max_capacity: Capacity | None = None

    @field_validator("title", "event_date", "location", "max_capacity", mode="before")
    @classmethod
    def reject_explicit_null(cls, value: Any) -> Any:
        """Reject `null` for fields whose database columns are NOT NULL.

        Validators do not run on default values, so leaving a field out still
        works; only a client that explicitly sends `null` reaches this check.
        Without it, the update would fail in the database with a 500 error.

        Args:
            value: The raw value sent by the client.

        Returns:
            The value unchanged when it is not None.

        Raises:
            ValueError: If the client sent `null` (Pydantic turns this into a 422).
        """
        if value is None:
            raise ValueError("this field cannot be null")
        return value


class EventRead(BaseModel):
    """Event as returned by the API.

    Attributes:
        id: Primary key.
        title: Short name of the event.
        description: Optional longer text about the event.
        event_date: Calendar day the event takes place.
        location: Where the event is held.
        max_capacity: Maximum number of attendees.
        created_at: When the event was created.
        updated_at: When the event was last changed.
    """

    # from_attributes lets FastAPI build this schema straight from an ORM Event.
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    event_date: date
    location: str
    max_capacity: int
    created_at: datetime
    updated_at: datetime
