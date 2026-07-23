"""Message service: the use-case orchestrator.

Coordinates the processing pipeline and the repository to fulfill the two
use cases: create a processed message, and list a session's messages. It
depends on abstractions (the repository protocol, a list of steps), never on
concrete implementations — this is where dependency injection pays off.
"""

from app.models.message import Message
from app.repositories.base import MessageRepository
from app.schemas.message import MessageCreate
from app.services.pipeline import run_pipeline
from app.services.pipeline.base import ProcessingStep


class MessageService:
    """Application use cases for chat messages."""

    def __init__(
        self,
        repository: MessageRepository,
        pipeline_steps: list[ProcessingStep],
    ) -> None:
        self._repository = repository
        self._steps = pipeline_steps

    def create_message(self, payload: MessageCreate) -> Message:
        """Process an incoming message and persist it.

        Raises:
            DuplicateMessageError: if the message_id already exists.
        """
        result = run_pipeline(payload, self._steps)

        message = Message(
            message_id=payload.message_id,
            session_id=payload.session_id,
            content=result.content,
            sender=payload.sender,
            timestamp=payload.timestamp,
            word_count=result.word_count,
            character_count=result.character_count,
            processed_at=result.processed_at,
        )
        return self._repository.add(message)

    def list_session_messages(
        self,
        session_id: str,
        *,
        limit: int,
        offset: int,
        sender: str | None = None,
    ) -> tuple[list[Message], int]:
        """Return a page of a session's messages plus the total match count."""
        return self._repository.list_by_session(
            session_id, limit=limit, offset=offset, sender=sender
        )

    def search_messages(
        self,
        query: str,
        *,
        limit: int,
        offset: int,
        session_id: str | None = None,
    ) -> tuple[list[Message], int]:
        """Search stored messages by content, optionally scoped to a session."""
        return self._repository.search(
            query, limit=limit, offset=offset, session_id=session_id
        )
