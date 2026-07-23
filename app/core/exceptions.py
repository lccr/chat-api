"""Domain exception hierarchy.

Services and repositories raise these framework-agnostic exceptions; the API
layer translates them into the uniform error envelope.
"""

from typing import Any


class DomainError(Exception):
    """Base class for all expected application errors.

    Attributes:
        code: Stable, machine-readable error code (e.g. ``INVALID_FORMAT``).
        message: Human-readable summary of the problem.
        details: Optional context (field names, offending values, ...).
        status_code: HTTP status the API layer should respond with.
    """

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidFormatError(DomainError):
    """The payload is syntactically or semantically invalid."""

    code = "INVALID_FORMAT"
    status_code = 422


class DuplicateMessageError(DomainError):
    """A message with the same ``message_id`` already exists."""

    code = "DUPLICATE_MESSAGE"
    status_code = 409


class NotFoundError(DomainError):
    """The requested resource does not exist."""

    code = "NOT_FOUND"
    status_code = 404

class UnauthorizedError(DomainError):
    """Authentication failed: missing or invalid API key."""

    code = "UNAUTHORIZED"
    status_code = 401

class RateLimitExceededError(DomainError):
    """Too many requests from the same client."""

    code = "RATE_LIMIT_EXCEEDED"
    status_code = 429
