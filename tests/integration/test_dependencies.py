"""Tests for the unit-of-work session dependency.

These exercise the *real* get_db_session (made injectable in the deps
refactor) to verify its commit-on-success / rollback-on-error boundary,
without replicating its logic.
"""

from collections.abc import Iterator

import pytest
from app.api.deps import get_db_session
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

pytestmark = pytest.mark.integration


@pytest.fixture()
def engine() -> Iterator[Engine]:
    """Isolated in-memory engine with a scratch table."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)"))
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture()
def factory(engine: Engine) -> sessionmaker[Session]:
    """A session factory bound to the test engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def _rows(factory: sessionmaker[Session]) -> list[tuple[str]]:
    session = factory()
    try:
        return session.execute(text("SELECT v FROM t")).fetchall()  # type: ignore[return-value]
    finally:
        session.close()


class TestUnitOfWorkSession:
    """get_db_session commits on success and rolls back on error."""

    def test_commits_when_the_block_succeeds(self, factory: sessionmaker[Session]) -> None:
        gen = get_db_session(factory)
        session = next(gen)
        session.execute(text("INSERT INTO t (v) VALUES ('kept')"))
        with pytest.raises(StopIteration):
            next(gen)  # generator completes -> commit runs

        assert _rows(factory) == [("kept",)]

    def test_rolls_back_when_the_block_raises(self, factory: sessionmaker[Session]) -> None:
        gen = get_db_session(factory)
        session = next(gen)
        session.execute(text("INSERT INTO t (v) VALUES ('discarded')"))
        with pytest.raises(ValueError):
            gen.throw(ValueError("boom"))  # error thrown into the block -> rollback

        assert _rows(factory) == []
