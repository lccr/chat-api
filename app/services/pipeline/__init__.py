"""Message processing pipeline assembly.

Builds the ordered list of processing steps and runs a message through them.
The order matters: filtering runs before enrichment so metadata describes the
final, censored content.
"""

from app.schemas.message import MessageCreate
from app.services.pipeline.base import ProcessingResult, ProcessingStep
from app.services.pipeline.content_filter import ContentFilterStep
from app.services.pipeline.metadata_enricher import MetadataEnricherStep


def build_pipeline(banned_words: list[str]) -> list[ProcessingStep]:
    """Assemble the ordered processing steps.

    Order is a design decision: the content filter must run before the
    metadata enricher so counts reflect the stored (censored) content.
    """
    return [
        ContentFilterStep(banned_words),
        MetadataEnricherStep(),
    ]


def run_pipeline(
    message: MessageCreate, steps: list[ProcessingStep]
) -> ProcessingResult:
    """Thread a message through every step and return the final result."""
    result = ProcessingResult(content=message.content)
    for step in steps:
        result = step.process(message, result)
    return result
