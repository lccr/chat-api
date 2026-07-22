# 1. Framework and layered architecture

Date: 2026-07-22

## Status

Accepted

## Context

The assessment allows either Flask or FastAPI and asks for clean
architecture, dependency injection, SOLID principles, request validation,
robust error handling and a test suite. A framework and an overall structure
must be chosen before any code is written.

## Decision

Use **FastAPI** with a layered structure — api / services / repositories /
schemas / core — where dependencies point inward only: the api layer knows
the services, the services know the repository abstraction, and the domain
(services, pipeline, models) never imports the web framework.

## Consequences

- Pydantic provides declarative request validation and typed contracts; the
  schema requirements map directly to model definitions.
- FastAPI's dependency injection enables constructor-style wiring and trivial
  overrides in tests, with no extra container library.
- OpenAPI documentation is generated from the same source of truth as the
  validation, so docs cannot drift from behavior.
- The async-native foundation keeps the optional WebSocket feature idiomatic.
- Because the domain never imports FastAPI, the same services, pipeline and
  repository could be rehosted under Flask by rewriting only the api layer —
  the basis for the planned mirror implementation.