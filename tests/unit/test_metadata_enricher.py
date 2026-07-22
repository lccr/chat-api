"""Unit tests for the metadata enrichment step."""

from datetime import datetime, timezone

import pytest
from app.schemas.message import MessageCreate
from app.services.pipeline.base import ProcessingResult
from app.services.pipeline.metadata_enricher import MetadataEnricherStep

pytestmark = pytest.mark.unit


def _enrich(content: str) -> ProcessingResult:
    """Run the enricher over a piece of content and return the result."""
    message = MessageCreate(
        message_id="m",
        session_id="s",
        content=content,
        sender="user",
        timestamp="2023-06-15T14:30:00Z",
    )
    return MetadataEnricherStep().process(message, ProcessingResult(content=content))


class TestMetadataEnricher:
    """Behavior of the metadata enrichment step."""

    @pytest.mark.parametrize(
        ("content", "expected_words", "expected_chars"),
        [
            ("hello world", 2, 11),
            ("one", 1, 3),
            ("a b c d e", 5, 9),
            ("multiple   spaces   here", 3, 24),
            ("  leading and trailing  ", 3, 24),
            ("emoji 🎉 counts", 3, 14),
        ],
    )
    def test_counts_words_and_characters(
        self, content: str, expected_words: int, expected_chars: int
    ) -> None:
        result = _enrich(content)
        assert result.word_count == expected_words
        assert result.character_count == expected_chars

    def test_sets_processed_at_to_utc_aware_datetime(self) -> None:
        result = _enrich("anything")
        assert result.processed_at is not None
        assert result.processed_at.tzinfo == timezone.utc

    def test_processed_at_is_recent(self) -> None:
        before = datetime.now(timezone.utc)
        result = _enrich("anything")
        after = datetime.now(timezone.utc)
        assert result.processed_at is not None
        assert before <= result.processed_at <= after
