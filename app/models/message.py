"""Message ORM model."""

from datetime import datetime

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Message(Base):
    """Persisted chat message.

    ``message_id`` is the business identifier supplied by the client and is
    unique; ``id`` is the internal surrogate primary key.
    """

    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("message_id", name="uq_messages_message_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # message_id,  No index=True,  the UniqueConstraint already creates one.
    message_id: Mapped[str] = mapped_column(String(255))
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(String)
    sender: Mapped[str] = mapped_column(String(16))
    timestamp: Mapped[datetime] = mapped_column()

    # Enrichment metadata produced by the processing pipeline.
    word_count: Mapped[int] = mapped_column()
    character_count: Mapped[int] = mapped_column()
    processed_at: Mapped[datetime] = mapped_column()
