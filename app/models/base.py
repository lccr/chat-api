"""SQLAlchemy declarative base.

A single ``Base`` class that all ORM models inherit from; SQLAlchemy uses it
to collect metadata (table definitions) for schema creation and queries.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
