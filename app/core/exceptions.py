"""Domain exceptions raised by services and mapped to HTTP responses in main.py.

Services raise these instead of `HTTPException`, so business logic stays
independent of the web framework and one handler decides the status codes.
"""


class DomainError(Exception):
    """Base class for all expected business-rule failures.

    Attributes:
        status_code: HTTP status the exception handler responds with.
        message: Human-readable explanation sent as the response `detail`.
    """

    status_code: int = 400

    def __init__(self, message: str) -> None:
        """Store the message for the exception handler.

        Args:
            message: Human-readable explanation of the failure.
        """
        super().__init__(message)
        self.message = message


class EventNotFoundError(DomainError):
    """Raised when no event exists with the requested id."""

    status_code = 404

    def __init__(self, event_id: int) -> None:
        """Build the message from the missing event's id.

        Args:
            event_id: The id that was looked up.
        """
        super().__init__(f"Event {event_id} not found")
