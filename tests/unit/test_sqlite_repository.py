"""Unit tests for the SQLite repository, over an in-memory database."""

from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from app.core.exceptions import DuplicateMessageError
from app.models.base import Base
from app.models.message import Message
from app.repositories.sqlite_repository import SqliteMessageRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

pytestmark = pytest.mark.unit


@pytest.fixture()
def session() -> Iterator[Session]:
    """An isolated in-memory session with the schema created."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = factory()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _message(message_id: str, session_id: str = "s1", sender: str = "user") -> Message:
    now = datetime.now(timezone.utc)
    return Message(
        message_id=message_id,
        session_id=session_id,
        content="hi",
        sender=sender,
        timestamp=now,
        word_count=1,
        character_count=2,
        processed_at=now,
    )


class TestSqliteMessageRepository:
    """Persistence behavior of the concrete repository."""

    def test_add_persists_and_returns_message(self, session: Session) -> None:
        repo = SqliteMessageRepository(session)
        result = repo.add(_message("m1"))
        session.commit()
        assert result.message_id == "m1"

    def test_add_duplicate_raises_domain_error(self, session: Session) -> None:
        """IntegrityError from the unique constraint is translated to a domain error."""
        repo = SqliteMessageRepository(session)
        repo.add(_message("dup"))
        session.commit()
        with pytest.raises(DuplicateMessageError):
            repo.add(_message("dup"))

    def test_exists_reflects_stored_messages(self, session: Session) -> None:
        repo = SqliteMessageRepository(session)
        repo.add(_message("present"))
        session.commit()
        assert repo.exists("present") is True
        assert repo.exists("absent") is False
