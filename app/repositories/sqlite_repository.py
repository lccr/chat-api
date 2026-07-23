"""SQLAlchemy-backed message repository.

Concrete implementation of the ``MessageRepository`` protocol. It does not
inherit from the protocol (structural typing): mypy verifies conformance at
the point of injection.
"""

from sqlalchemy import func, select, text
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

    def search(
        self,
        query: str,
        *,
        limit: int,
        offset: int,
        session_id: str | None = None,
    ) -> tuple[list[Message], int]:
        """Search message content using the FTS5 index, ranked by relevance."""
        # FTS5 treats several characters as query syntax; quoting the term
        # makes it a literal phrase and avoids syntax errors on user input.
        match_expression = f'"{query}"'

        conditions = ["messages_fts MATCH :match"]
        params: dict[str, object] = {"match": match_expression}
        if session_id is not None:
            conditions.append("m.session_id = :session_id")
            params["session_id"] = session_id
        where_clause = " AND ".join(conditions)

        total_sql = text(
            f"SELECT count(*) FROM messages_fts "  # noqa: S608
            f"JOIN messages m ON m.id = messages_fts.rowid WHERE {where_clause}"
        )
        total = self._session.scalar(total_sql, params) or 0

        rows_sql = text(
            f"SELECT m.id FROM messages_fts "  # noqa: S608
            f"JOIN messages m ON m.id = messages_fts.rowid WHERE {where_clause} "
            f"ORDER BY rank LIMIT :limit OFFSET :offset"
        )
        ids = list(
            self._session.scalars(rows_sql, {**params, "limit": limit, "offset": offset})
        )
        if not ids:
            return [], total

        # Re-fetch as ORM objects, preserving the relevance order from FTS.
        messages = list(self._session.scalars(select(Message).where(Message.id.in_(ids))))
        by_id = {m.id: m for m in messages}
        ordered = [by_id[i] for i in ids if i in by_id]
        return ordered, total
