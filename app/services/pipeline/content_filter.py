"""Content filtering step.

Censors banned words by replacing each with asterisks of equal length. This
is a *transformation*: the message is stored (censored), not rejected, which
keeps every pipeline step a pure transformer over the ProcessingResult.
"""

import re

from app.schemas.message import MessageCreate
from app.services.pipeline.base import ProcessingResult


class ContentFilterStep:
    """Replace configured banned words with asterisks."""

    def __init__(self, banned_words: list[str]) -> None:
        # Precompile one case-insensitive pattern with word boundaries.
        # Empty word list -> no-op pattern that never matches.
        self._pattern: re.Pattern[str] | None = None
        if banned_words:
            escaped = [re.escape(word) for word in banned_words]
            self._pattern = re.compile(
                r"\b(" + "|".join(escaped) + r")\b",
                flags=re.IGNORECASE,
            )

    def process(self, message: MessageCreate, result: ProcessingResult) -> ProcessingResult:
        """Censor banned words in the current content."""
        if self._pattern is None:
            return result
        result.content = self._pattern.sub(
            lambda match: "*" * len(match.group()),
            result.content,
        )
        return result
