"""Message request/response schemas.

These Pydantic models are the API contract: they validate incoming payloads
and shape outgoing responses. They are distinct from the ORM model — the wire
format is decoupled from the storage format.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Sender = Literal["user", "system"]


class MessageCreate(BaseModel):
    """Incoming payload for creating a message."""

    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=1, max_length=255)
    session_id: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    timestamp: datetime
    sender: Sender

    @field_validator("timestamp")
    @classmethod
    def ensure_utc_aware(cls, value: datetime) -> datetime:
        """Normalize the timestamp to a UTC-aware datetime.

        Naive datetimes (no timezone) are assumed to be UTC; aware datetimes
        in other zones are converted to UTC. This guarantees every stored
        timestamp is comparable and unambiguous.
        """
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)  # pragma: no cover
        return value.astimezone(timezone.utc)


class MessageMetadata(BaseModel):
    """Enrichment metadata produced by the processing pipeline."""

    word_count: int
    character_count: int
    processed_at: datetime


class MessageResponse(BaseModel):
    """Outgoing representation of a stored message."""

    model_config = ConfigDict(from_attributes=True)

    message_id: str
    session_id: str
    content: str
    timestamp: datetime
    sender: Sender
    metadata: MessageMetadata
