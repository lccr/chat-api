"""Unit tests for the message service, using an in-memory fake repository.

The service depends on the MessageRepository *protocol*, so we can inject a
lightweight fake instead of SQLite. This isolates service logic (pipeline
orchestration + persistence coordination) from any real database.
"""

import pytest
from app.core.exceptions import DuplicateMessageError
from app.models.message import Message
from app.services.message_service import MessageService
from app.services.pipeline import build_pipeline

pytestmark = pytest.mark.unit


class FakeMessageRepository:
    """In-memory MessageRepository implementation for tests.

    Satisfies the protocol structurally — it never imports or inherits from
    it, yet is accepted wherever a MessageRepository is expected.
    """

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add(self, message: Message) -> Message:
        if any(m.message_id == message.message_id for m in self._messages):
            raise DuplicateMessageError(
                message="duplicate",
                details=f"message_id: {message.message_id}",
            )
        self._messages.append(message)
        return message

    def exists(self, message_id: str) -> bool:
        return any(m.message_id == message_id for m in self._messages)

    def list_by_session(
        self,
        session_id: str,
        *,
        limit: int,
        offset: int,
        sender: str | None = None,
    ) -> tuple[list[Message], int]:
        matches = [m for m in self._messages if m.session_id == session_id]
        if sender is not None:
            matches = [m for m in matches if m.sender == sender]
        return matches[offset : offset + limit], len(matches)


@pytest.fixture()
def service() -> MessageService:
    """A service wired to a fake repository and the real pipeline."""
    return MessageService(FakeMessageRepository(), build_pipeline(["badword"]))


class TestCreateMessage:
    """Behavior of MessageService.create_message."""

    def test_persists_and_returns_the_message(self, service, make_payload) -> None:
        result = service.create_message(make_payload(message_id="m1"))
        assert result.message_id == "m1"

    def test_runs_the_pipeline_censoring_content(self, service, make_payload) -> None:
        result = service.create_message(make_payload(content="hello badword"))
        assert result.content == "hello *******"

    def test_populates_metadata(self, service, make_payload) -> None:
        result = service.create_message(make_payload(content="one two three"))
        assert result.word_count == 3
        assert result.character_count == 13
        assert result.processed_at is not None

    def test_rejects_duplicate_message_id(self, service, make_payload) -> None:
        service.create_message(make_payload(message_id="dup"))
        with pytest.raises(DuplicateMessageError):
            service.create_message(make_payload(message_id="dup"))


class TestListSessionMessages:
    """Behavior of MessageService.list_session_messages."""

    def test_returns_only_the_requested_session(self, service, make_payload) -> None:
        service.create_message(make_payload(message_id="a", session_id="s1"))
        service.create_message(make_payload(message_id="b", session_id="s2"))
        messages, total = service.list_session_messages("s1", limit=10, offset=0)
        assert [m.message_id for m in messages] == ["a"]
        assert total == 1

    def test_filters_by_sender(self, service, make_payload) -> None:
        service.create_message(make_payload(message_id="a", sender="user"))
        service.create_message(make_payload(message_id="b", sender="system"))
        messages, total = service.list_session_messages(
            "sess-1", limit=10, offset=0, sender="system"
        )
        assert [m.message_id for m in messages] == ["b"]
        assert total == 1

    def test_paginates_with_limit_and_offset(self, service, make_payload) -> None:
        for i in range(5):
            service.create_message(make_payload(message_id=f"m{i}"))
        page, total = service.list_session_messages("sess-1", limit=2, offset=2)
        assert len(page) == 2
        assert total == 5
