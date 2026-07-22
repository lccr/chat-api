"""Unit tests for the content filter step."""

import pytest

from app.schemas.message import MessageCreate
from app.services.pipeline.base import ProcessingResult
from app.services.pipeline.content_filter import ContentFilterStep

pytestmark = pytest.mark.unit


def _run(step: ContentFilterStep, content: str) -> str:
    """Run the filter over a piece of content and return the result."""
    message = MessageCreate(
        message_id="m",
        session_id="s",
        content=content,
        sender="user",
        timestamp="2023-06-15T14:30:00Z",
    )
    return step.process(message, ProcessingResult(content=content)).content


class TestContentFilter:
    """Behavior of the banned-word censoring step."""

    def test_censors_a_banned_word(self) -> None:
        step = ContentFilterStep(["badword"])
        assert _run(step, "this is a badword here") == "this is a ******* here"

    def test_censoring_is_case_insensitive(self) -> None:
        step = ContentFilterStep(["badword"])
        assert _run(step, "BADWORD shouting") == "******* shouting"

    def test_does_not_censor_substrings(self) -> None:
        """The Scunthorpe problem: 'badword' must not match inside 'badwordy'."""
        step = ContentFilterStep(["badword"])
        assert _run(step, "this is badwordy text") == "this is badwordy text"

    def test_leaves_clean_content_untouched(self) -> None:
        step = ContentFilterStep(["badword"])
        assert _run(step, "a perfectly clean message") == "a perfectly clean message"

    def test_censors_multiple_distinct_words(self) -> None:
        step = ContentFilterStep(["foo", "bar"])
        assert _run(step, "foo and bar") == "*** and ***"

    def test_empty_banned_list_is_a_noop(self) -> None:
        step = ContentFilterStep([])
        assert _run(step, "badword stays") == "badword stays"

    def test_special_regex_characters_are_escaped(self) -> None:
        """A banned word with regex metacharacters must be matched literally."""
        step = ContentFilterStep(["a.b"])
        assert _run(step, "a.b is censored") == "*** is censored"
        assert _run(step, "axb is not") == "axb is not"
