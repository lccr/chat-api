# 2. Dependency inversion via protocols and a composition root

Date: 2026-07-22

## Status

Accepted

## Context

The layers defined in ADR-0001 must be wired together without coupling the
domain to concrete implementations. The service layer needs a repository and
a processing pipeline, but must not depend on SQLite or on how those
collaborators are constructed. Tests must be able to substitute fakes.

## Decision

Depend on **abstractions** expressed as `typing.Protocol`, and concentrate
all concrete choices in a single **composition root** (`app/api/deps.py`).

- `MessageRepository` and `ProcessingStep` are Protocols. Implementations
  satisfy them structurally — they neither import nor inherit from the
  Protocol — and are verified at the injection point by the type checker.
- Collaborators are passed through constructors (the service receives its
  repository and steps; the repository receives its session). Nothing reaches
  for global state.
- `deps.py` is the only module that names concrete classes and builds them.
  Application-scoped, stateless collaborators (pipeline steps, engine) are
  built once; request-scoped, stateful ones (the database session) are built
  per request.

## Consequences

- The service is tested with an in-memory fake repository and no database,
  proving the domain is decoupled from persistence.
- Swapping SQLite for another database changes one place — the composition
  root — not the domain.
- The database session dependency owns the unit-of-work boundary: it commits
  when the request handler returns normally and rolls back on any exception,
  while repositories only flush. This keeps a request atomic.
- Using Protocols over abstract base classes means implementations carry no
  dependency on the abstraction, at the cost that conformance is only checked
  where an implementation is actually injected.