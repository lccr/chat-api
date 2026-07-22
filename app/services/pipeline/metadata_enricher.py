"""Metadata enrichment step.

Computes word/character counts and the processing timestamp. Counts are taken
over the *processed* content (result.content), so the metadata always
describes the message as stored and returned, not an intermediate state.
"""

from datetime import datetime, timezone

from app.schemas.message import MessageCreate
from app.services.pipeline.base import ProcessingResult


class MetadataEnricherStep:
    """Populate word count, character count and processing timestamp."""

    def process(self, message: MessageCreate, result: ProcessingResult) -> ProcessingResult:
        """Enrich the result with computed metadata over the current content."""
        content = result.content
        result.character_count = len(content)
        result.word_count = len(content.split())
        result.processed_at = datetime.now(timezone.utc)
        return result
