"""Dependency wiring for the API layer.

This is the composition root: the single place where concrete implementations
are chosen and injected. Handlers depend on abstractions; this module decides
what fills them. It also owns the database session lifecycle, which is where
the unit-of-work commit/rollback lives.
"""
import secrets
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.repositories.sqlite_repository import SqliteMessageRepository
from app.services.message_service import MessageService
from app.services.pipeline import build_pipeline
from app.services.pipeline.base import ProcessingStep

# --- Application-scoped singletons (built once at import/startup) ---------

_settings = get_settings()

# SQLite needs check_same_thread=False because FastAPI may run sync
# endpoints across threads; the engine's connection pool is thread-safe.
_engine = create_engine(
    _settings.database_url,
    connect_args={"check_same_thread": False},
)
_SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)

# Pipeline steps are stateless and reusable: build them once, share them.
_pipeline_steps: list[ProcessingStep] = build_pipeline(_settings.banned_words_list)


def get_engine() -> Engine:
    """Expose the engine so startup code can create the schema."""
    return _engine

def get_session_factory() -> sessionmaker[Session]:
    """Return the application's session factory (overridable in tests)."""
    return _SessionFactory  # pragma: no cover  (overridden in tests)


# --- Request-scoped dependencies (built per request) ----------------------


def get_db_session(
    factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
) -> Iterator[Session]:
    """Provide a database session bound to the request lifecycle.

    Commits if the request handler returns normally; rolls back on any
    exception. This is the unit-of-work boundary: repositories flush, this
    dependency commits. The factory is injected so tests can supply their own.
    """
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_pipeline_steps() -> list[ProcessingStep]:
    """Return the application-wide pipeline steps."""
    return _pipeline_steps


def get_message_service(
    session: Annotated[Session, Depends(get_db_session)],
    steps: Annotated[list[ProcessingStep], Depends(get_pipeline_steps)],
) -> MessageService:
    """Assemble the message service for a request."""
    repository = SqliteMessageRepository(session)
    return MessageService(repository, steps)

def require_api_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """Enforce API-key authentication on protected endpoints.

    If no API key is configured (settings.api_key is empty), authentication is
    disabled — convenient for local development and tests. Otherwise a valid
    ``X-API-Key`` header is required.
    """
    if not settings.api_key:
        return
    if x_api_key is None or not secrets.compare_digest(x_api_key, settings.api_key):
        raise UnauthorizedError(
            message="Missing or invalid API key",
            details="Provide a valid X-API-Key header",
        )

SettingsDep = Annotated[Settings, Depends(get_settings)]
MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
