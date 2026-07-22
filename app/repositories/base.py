"""Repository interface.

Defines the persistence contract the service layer depends on. The service
knows only this Protocol, never a concrete database implementation — that is
Dependency Inversion: both layers depend on the abstraction, not on DB Engine (SQLite).
"""

from typing import Protocol

from app.models.message import Message


class MessageRepository(Protocol):
    """Persistence contract for chat messages."""

    def add(self, message: Message) -> Message:
        """Persist a new message and return it.

        Raises:
            DuplicateMessageError: if ``message_id`` already exists.
        """
        ...  # pragma: no cover

    def exists(self, message_id: str) -> bool:
        """Return whether a message with the given message id exists."""
        ...  # pragma: no cover

    def list_by_session(
        self,
        session_id: str,
        *,
        limit: int,
        offset: int,
        sender: str | None = None,
    ) -> tuple[list[Message], int]:
        """Return a page of messages for a session and the total count.

        The total is the unpaginated count matching the filters, needed so
        clients can compute how many pages exist.
        """
        ...  # pragma: no cover
