"""Response schemas for event registrations.

There is no request schema: registering takes no body, because the registrant
is always the logged-in user identified by the bearer token.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegistrantRead(BaseModel):
    """The public details of the user behind a registration.

    Attributes:
        full_name: The registrant's display name.
        email: The registrant's email address.
    """

    model_config = ConfigDict(from_attributes=True)

    full_name: str
    email: str


class RegistrationRead(BaseModel):
    """Registration as returned by the API.

    Attributes:
        id: Primary key; used to cancel the registration.
        event_id: Id of the event the user signed up for.
        registered_at: When the user signed up.
        user: Name and email of the registered user.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "event_id": 42,
                "registered_at": "2026-11-12T09:30:00Z",
                "user": {"full_name": "Ada Lovelace", "email": "ada.lovelace@acme.com"},
            }
        },
    )

    id: int
    event_id: int
    registered_at: datetime
    user: RegistrantRead
