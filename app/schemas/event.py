"""Request and response schemas for events."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    """Body for creating an event.

    Attributes:
        title: Short name of the event.
        description: Optional longer text about the event.
        event_date: Calendar day the event takes place.
        location: Where the event is held.
        max_capacity: Maximum number of attendees.
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

    title: str
    description: str | None = None
    event_date: date
    location: str
    max_capacity: int


class EventUpdate(BaseModel):
    """Body for updating an event; only the fields sent are changed.

    Attributes:
        title: New title, if changing it.
        description: New description, if changing it.
        event_date: New date, if changing it.
        location: New location, if changing it.
        max_capacity: New capacity, if changing it.
    """

    model_config = ConfigDict(
        json_schema_extra={"example": {"location": "Conference Room B", "max_capacity": 50}}
    )

    title: str | None = None
    description: str | None = None
    event_date: date | None = None
    location: str | None = None
    max_capacity: int | None = None


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
