# Core rules

Keep core focused on shared schemas, fields, DTO visibility, action contracts,
and dependency primitives. Put higher-layer execution and backend behavior
in their owning modules, following `.importlinter`.

Keep dependency resolution and resource scopes in `core.depends`; reuse them
from `core.context` and higher layers instead of creating parallel machinery.

Use `Schema` for contracts shared by FastSprout dataclasses, `typed_fields`
objects, and `BaseSchema`. Do not narrow those contracts to Pydantic models.
Declare DTO visibility on source fields once and preserve both runtime guards
and the static restrictions of class-based DTOs. Support standard mypy and
Pylance/basedpyright without custom checker patches or generated declarations.
