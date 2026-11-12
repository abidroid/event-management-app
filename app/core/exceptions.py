"""Domain exceptions raised by services and mapped to HTTP responses in main.py.

Services raise these instead of `HTTPException`, so business logic stays
independent of the web framework and one handler decides the status codes.
"""


class DomainError(Exception):
    """Base class for all expected business-rule failures.

    Attributes:
        status_code: HTTP status the exception handler responds with.
        headers: Extra response headers, or None when none are needed.
        message: Human-readable explanation sent as the response `detail`.
    """

    status_code: int = 400
    headers: dict[str, str] | None = None

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


class RegistrationNotFoundError(DomainError):
    """Raised when no registration exists with the requested id."""

    status_code = 404

    def __init__(self, registration_id: int) -> None:
        """Build the message from the missing registration's id.

        Args:
            registration_id: The id that was looked up.
        """
        super().__init__(f"Registration {registration_id} not found")


class DuplicateRegistrationError(DomainError):
    """Raised when the current user is already registered for the event."""

    status_code = 409

    def __init__(self, event_id: int) -> None:
        """Build the message from the event's id.

        Args:
            event_id: The event the user tried to register for again.
        """
        super().__init__(f"You are already registered for event {event_id}")


class EventFullError(DomainError):
    """Raised when an event has no seats left."""

    status_code = 409

    def __init__(self, event_id: int) -> None:
        """Build the message from the full event's id.

        Args:
            event_id: The event that has reached its capacity.
        """
        super().__init__(f"Event {event_id} is full")


class CapacityBelowRegistrationsError(DomainError):
    """Raised when an update would set capacity below the current sign-ups."""

    status_code = 409

    def __init__(self, max_capacity: int, registered_count: int) -> None:
        """Build the message from the requested capacity and current sign-ups.

        Args:
            max_capacity: The capacity the client asked for.
            registered_count: How many people are already registered.
        """
        super().__init__(
            f"Capacity {max_capacity} is below the {registered_count} people "
            "already registered"
        )


class NotRegistrationOwnerError(DomainError):
    """Raised when a user tries to cancel someone else's registration."""

    status_code = 403

    def __init__(self, registration_id: int) -> None:
        """Build the message; the id is kept for debugging but not revealed.

        Args:
            registration_id: The registration the user tried to cancel.
        """
        super().__init__("You can only cancel your own registrations")
        self.registration_id = registration_id


class EmailAlreadyRegisteredError(DomainError):
    """Raised when someone signs up with an email that already has an account."""

    status_code = 409

    def __init__(self, email: str) -> None:
        """Build the message from the email that is taken.

        Args:
            email: The email address the client tried to register.
        """
        super().__init__(f"Email {email} is already registered")


class InvalidCredentialsError(DomainError):
    """Raised when a login fails or a bearer token is missing, invalid or expired."""

    status_code = 401

    def __init__(self, message: str = "Could not validate credentials") -> None:
        """Store the message and the header that asks for a Bearer token.

        Args:
            message: Human-readable explanation of the failure.
        """
        super().__init__(message)
        # The HTTP spec requires a 401 to tell the client which auth scheme to use.
        self.headers = {"WWW-Authenticate": "Bearer"}
