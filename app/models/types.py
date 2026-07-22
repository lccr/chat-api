"""Custom SQLAlchemy column types.

SQLite has no timezone-aware datetime type: it stores datetimes as text and
returns them naive. This decorator guarantees every datetime is stored and
retrieved as a UTC-aware value, so timezone information survives a round trip.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Dialect
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """A DateTime that always stores and returns UTC-aware values."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        """Normalize to UTC just before writing to the database."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        """Re-attach UTC when reading a naive datetime back from storage."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)  # pragma: no cover  (SQLite returns naive)
