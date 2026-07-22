# 5. Uniform error envelope with domain exception translation

Date: 2026-07-22

## Status

Accepted

## Context

The assessment requires robust, user-friendly error handling with appropriate
HTTP status codes and a consistent error response shape. Errors arise from
several sources: invalid payloads, business rule violations (duplicate id),
missing resources, framework routing errors (404, 405), and unexpected
failures.

## Decision

Every response — success or error — shares one top-level envelope. Errors are
modeled as a `DomainError` hierarchy raised by the domain, each carrying a
stable machine-readable `code` and an HTTP `status_code`. Centralized
exception handlers translate exceptions into the error envelope at the API
boundary; the domain never raises framework HTTP exceptions.

## Consequences

- The domain raises framework-agnostic errors (`InvalidFormatError`,
  `DuplicateMessageError`, `NotFoundError`), so business logic could be
  rehosted under another framework by rewriting only the handlers.
- Four handlers cover four failure classes: domain errors, request-validation
  errors, framework HTTP errors, and any unhandled exception. No endpoint can
  leak FastAPI's default 422 body, Starlette's default 404 body, or a stack
  trace.
- FastAPI's `RequestValidationError` is intercepted and reflattened into the
  envelope, so validation failures use the same shape as every other error.
- The last-resort handler logs the full exception server-side and returns a
  generic message to the client ("log everything, expose nothing"), avoiding
  information disclosure.
- Error codes are stable and distinct from HTTP status, so clients can branch
  on `code` without parsing human-readable messages. New error types are added
  by subclassing `DomainError` with a `code` and `status_code` — four lines,
  no changes to the handlers (Open/Closed).