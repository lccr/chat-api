# 3. Extensible processing pipeline with content censoring

Date: 2026-07-22

## Status

Accepted

## Context

The assessment requires a processing pipeline that validates the message,
filters inappropriate content, and adds metadata (word count, character
count, processing timestamp). The design must make it easy to add processing
steps later without destabilizing existing ones.

## Decision

Model the pipeline as an ordered list of independent **steps**, each
conforming to a `ProcessingStep` Protocol and transforming a shared,
mutable `ProcessingResult`. Adding behavior means appending a step, never
editing an existing one (Open/Closed).

For inappropriate content, the filter **censors** banned words by replacing
them with asterisks of equal length, and stores the censored message. It does
not reject the message.

## Consequences

- Format validation is not a pipeline step: it happens earlier, declaratively,
  in the Pydantic schemas at the API boundary. The pipeline only performs
  business-level processing (censoring, enrichment).
- Step order is significant and intentional: the filter runs before the
  enricher, so metadata describes the stored (censored) content.
- Word-boundary matching (`\b`) avoids censoring substrings of larger words
  (the "Scunthorpe problem"); banned words are regex-escaped so metacharacters
  are treated literally.
- Censoring keeps every step a pure transformer, consistent with the enricher.
  A reject-on-violation policy was considered; it was not made a configuration
  flag because the pipeline is already extensible by design — a rejecting
  policy would be an alternative step, not a conditional branch. Choosing one
  documented behavior avoids doubling the test and documentation surface for a
  need the assessment does not state.