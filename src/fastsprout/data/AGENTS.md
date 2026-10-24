# Data rules

DataR routes through backend and capability protocols. Reuse those contracts,
queries, and streams instead of introducing parallel CRUD or join APIs.
Keep shared contracts independent of SQLModel and SQLAlchemy; SQL-specific
behavior belongs in `backend/sql`.

Preserve entity and value type bounds through stream transformations. Reuse
`AnyIterable` and `resolve_any_iterable` for sync and async sources.
Joined streams must share one DataR context, including manually built joins.

Chunking limits memory use; it must not define transaction boundaries.
Publish data change events only after a successful commit and discard them
on rollback.

The sole private-import exception is `typing._ProtocolMeta` in
`src/fastsprout/data/backend/sql/entity.py`: it preserves protocol metaclass
compatibility and static entity types without separate runtime and
type-checking definitions.
