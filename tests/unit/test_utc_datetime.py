"""Unit tests for the UTCDateTime column type."""

from datetime import datetime, timezone

import pytest
from app.models.types import UTCDateTime
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, insert, select

pytestmark = pytest.mark.unit


@pytest.fixture()
def table_and_engine():
    """A one-column table using UTCDateTime over an in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    table = Table(
        "sample",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("ts", UTCDateTime),
    )
    metadata.create_all(engine)
    try:
        yield table, engine
    finally:
        engine.dispose()


def _round_trip(table, engine, value):
    with engine.begin() as conn:
        conn.execute(insert(table).values(id=1, ts=value))
    with engine.connect() as conn:
        return conn.execute(select(table.c.ts)).scalar_one()


class TestUTCDateTime:
    """The custom type stores and returns UTC-aware datetimes."""

    def test_naive_is_stored_and_returned_as_utc(self, table_and_engine) -> None:
        table, engine = table_and_engine
        naive = datetime(2023, 6, 15, 14, 30, 0)
        result = _round_trip(table, engine, naive)
        assert result.tzinfo == timezone.utc
        assert result.hour == 14

    def test_aware_non_utc_is_converted_to_utc(self, table_and_engine) -> None:
        from datetime import timedelta

        table, engine = table_and_engine
        bogota = timezone(timedelta(hours=-5))
        aware = datetime(2023, 6, 15, 14, 30, 0, tzinfo=bogota)
        result = _round_trip(table, engine, aware)
        assert result.tzinfo == timezone.utc
        assert result.hour == 19  # 14:30 -05:00 -> 19:30 UTC

    def test_none_is_preserved(self, table_and_engine) -> None:
        table, engine = table_and_engine
        result = _round_trip(table, engine, None)
        assert result is None
