"""SQLAlchemy-backed message repository.

Concrete implementation of the ``MessageRepository`` protocol. It does not
inherit from the protocol (structural typing): mypy verifies conformance at
the point of injection.
"""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateMessageError
from app.models.message import Message


class SqliteMessageRepository:
    """Persist and query messages using a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, message: Message) -> Message:
        """Persist a new message, translating a unique-key clash to a domain error."""
        self._session.add(message)
        try:
            # use flush() instead of commit() to avoid committing the transaction here;
            # the service layer controls the transaction boundary.
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise DuplicateMessageError(
                message="A message with this message_id already exists",
                details=f"message_id: {message.message_id}",
            ) from exc
        return message

    def exists(self, message_id: str) -> bool:
        """Return whether a message with the given business id exists."""
        stmt = select(Message.id).where(Message.message_id == message_id).limit(1)
        return self._session.scalar(stmt) is not None

    def list_by_session(
        self,
        session_id: str,
        *,
        limit: int,
        offset: int,
        sender: str | None = None,
    ) -> tuple[list[Message], int]:
        """Return a page of messages for a session plus the total match count."""
        filters = [Message.session_id == session_id]
        if sender is not None:
            filters.append(Message.sender == sender)

        total = self._session.scalar(
            select(func.count()).select_from(Message).where(*filters)
        )

        stmt = (
            select(Message)
            .where(*filters)
            .order_by(Message.timestamp.asc())
            .limit(limit)
            .offset(offset)
        )
        messages = list(self._session.scalars(stmt).all())
        return messages, total or 0
