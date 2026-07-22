"""Processing pipeline abstractions.

A message is processed by a sequence of independent steps. Each step receives
the in-progress result and returns an updated one. New behavior is added by
appending a step, never by modifying existing ones — Open/Closed in practice.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.schemas.message import MessageCreate


@dataclass
class ProcessingResult:
    """Mutable carrier threaded through the pipeline.

    Starts from the validated input and accumulates the content
    transformations and metadata each step contributes.
    """

    content: str
    word_count: int = 0
    character_count: int = 0
    processed_at: datetime | None = None
    metadata: dict[str, object] = field(default_factory=dict)


class ProcessingStep(Protocol):
    """A single transformation in the processing pipeline."""

    def process(self, message: MessageCreate, result: ProcessingResult) -> ProcessingResult:
        """Apply this step's transformation and return the updated result."""
        ...  # pragma: no cover
