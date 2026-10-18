"""Explicit CRUD schemas with the entity as their default."""

from collections.abc import Mapping

from fastsprout.core import (
    UndefinedType,
)
from fastsprout.core.dto.base import DTO
from fastsprout.data.entity import Entitieable
from fastsprout.data.types import Valuable

from ..simple_service import Service
from .types import DataSOperation, SchemaSetting

__all__ = [
    "SCHEMA_OPERATIONS",
    "SchemaSetting",
    "configure_schemas",
    "install_schema",
    "read_source",
]


SCHEMA_OPERATIONS: dict[str, frozenset[DataSOperation]] = {
    "read_schema": frozenset(
        {
            "get",
            "list",
            "create",
            "update",
            "patch",
            "bulk_create",
            "bulk_update",
            "bulk_patch",
        }
    ),
    "create_schema": frozenset({"create", "bulk_create"}),
    "update_schema": frozenset({"update", "bulk_update"}),
    "patch_schema": frozenset({"patch", "bulk_patch"}),
}


def install_schema[S](
    target: Service,
    name: str,
    default: type[S],
    configured: SchemaSetting[S],
) -> frozenset[DataSOperation]:
    inherited = getattr(target, name, default)
    schema = inherited if isinstance(configured, UndefinedType) else configured
    setattr(
        target, name, schema if schema is not None else inherited or default
    )
    return SCHEMA_OPERATIONS[name] if schema is None else frozenset()


def configure_schemas[E, S](
    target: Service,
    source: type[E],
    overrides: Mapping[str, SchemaSetting[S]],
) -> frozenset[DataSOperation]:
    return frozenset().union(
        *(
            install_schema(target, name, source, schema)
            for name, schema in overrides.items()
        )
    )


def read_source(
    read: type[Valuable | Entitieable], source: type[Entitieable]
) -> type[DTO | Entitieable]:
    if read is source:
        return source
    if (
        issubclass(read, DTO)
        and "read" in read.__fastsprout_operations__
        and read.__fastsprout_source__ is source
    ):
        return read
    raise TypeError("read must be the entity or a read DTO derived from it")
