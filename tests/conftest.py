"""Shared pytest fixtures.

Fixtures defined here are auto-discovered by every test under tests/ without
explicit imports. They provide the building blocks the suite reuses: a valid
payload factory, an in-memory database, and an HTTP client wired to it.
"""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from app.api.deps import get_db_session
from app.main import create_app
from app.models.base import Base
from app.schemas.message import MessageCreate
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def make_payload() -> Callable[..., MessageCreate]:
    """Return a factory that builds valid MessageCreate payloads.

    Defaults produce a valid message; keyword overrides let each test vary
    only the field under test, keeping tests focused and readable.
    """

    def _factory(**overrides: Any) -> MessageCreate:
        data: dict[str, Any] = {
            "message_id": "msg-1",
            "session_id": "sess-1",
            "content": "hello world",
            "timestamp": "2023-06-15T14:30:00Z",
            "sender": "user",
        }
        data.update(overrides)
        return MessageCreate(**data)

    return _factory


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """Provide an isolated in-memory database session per test.

    Each test gets a fresh SQLite database in memory: full isolation, no disk,
    no cleanup, and tests can run in any order without interfering.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def app(db_session: Session) -> FastAPI:
    """Build an app whose database dependency is overridden to the test session.

    This is the payoff of dependency injection: the real get_db_session is
    replaced by one yielding the in-memory session, so integration tests hit
    the full stack without touching the production database.
    """
    application = create_app()

    def override_get_db_session() -> Iterator[Session]:
        yield db_session

    application.dependency_overrides[get_db_session] = override_get_db_session
    return application


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    """HTTP client against the full app, error handlers included."""
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
