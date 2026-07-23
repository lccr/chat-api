"""Shared pytest fixtures.

Fixtures defined here are auto-discovered by every test under tests/ without
explicit imports. They provide the building blocks the suite reuses: a valid
payload factory, an in-memory database, and an HTTP client wired to it.
"""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from app.api.deps import get_session_factory
from app.main import create_app
from app.models.base import Base
from app.models.fts import create_fts_schema
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
def db_engine():
    """Provide an isolated in-memory database engine per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    create_fts_schema(engine)
    try:
        yield engine
    finally:
        engine.dispose()

@pytest.fixture()
def app(db_engine) -> FastAPI:
    """Build an app whose session factory is overridden to the test engine.

    Overriding get_session_factory (not get_db_session) means the real
    unit-of-work dependency runs in tests, exercising its commit/rollback.
    """
    application = create_app()
    test_factory = sessionmaker(bind=db_engine, expire_on_commit=False)

    def override_get_session_factory() -> sessionmaker[Session]:
        return test_factory

    application.dependency_overrides[get_session_factory] = override_get_session_factory
    return application


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    """HTTP client against the full app, error handlers included."""
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
