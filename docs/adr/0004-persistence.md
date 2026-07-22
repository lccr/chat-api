# 4. SQLite persistence with a repository seam

Date: 2026-07-22

## Status

Accepted

## Context

The assessment mandates SQLite for simplicity and easy startup. The system
should also be deployable, and a production deployment would have different
persistence needs (concurrency, durability, schema evolution).

## Decision

Use SQLite through SQLAlchemy 2.0, behind the `MessageRepository` seam from
ADR-0002. Create the schema at startup with `Base.metadata.create_all`.
Persist all datetimes through a custom `UTCDateTime` type.

## Consequences

- The schema uses a surrogate integer primary key (`id`) distinct from the
  business identifier (`message_id`), which is enforced unique. This decouples
  the physical schema from a client-controlled value and keeps joins and
  indexes efficient.
- `create_all` is sufficient for this scope but does not handle schema
  *changes*: a production system would use versioned, reversible migrations
  (e.g. Alembic). Migrations are deliberately out of scope here.
- SQLite stores datetimes without timezone and returns them naive. The
  `UTCDateTime` type normalizes on write and re-attaches UTC on read, so
  timezone information survives the round trip and every endpoint serializes
  timestamps consistently.
- SQLite is single-writer and file-based, which constrains cloud deployment:
  serverless targets with ephemeral filesystems or multiple instances are
  unsuitable without a shared, persistent volume. Because persistence sits
  behind the repository seam, migrating to a managed database (Cloud SQL, RDS,
  or a serverless Postgres) changes only the composition root and the
  connection string, not the domain.