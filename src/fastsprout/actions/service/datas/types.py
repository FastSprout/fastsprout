"""Operation names, schema settings, and paginated responses."""

from typing import Annotated, ClassVar, Literal

from pydantic import ConfigDict
from pydantic import Field as PydanticField

from fastsprout.core import BaseSchema, UndefinedType

__all__ = [
    "DataSOperation",
    "Page",
    "SchemaSetting",
    "WriteOperation",
]

type DataSOperation = Literal[
    "project",
    "find_first",
    "find_exactly_one",
    "find_all",
    "iter",
    "get",
    "exists",
    "list",
    "count",
    "create",
    "update",
    "patch",
    "delete",
    "bulk_create",
    "upsert",
    "bulk_upsert",
    "update_by_query",
    "delete_by_query",
    "bulk_update",
    "bulk_patch",
    "bulk_delete",
]
type WriteOperation = Literal[
    "create",
    "update",
    "patch",
    "delete",
    "bulk_create",
    "upsert",
    "bulk_upsert",
    "update_by_query",
    "delete_by_query",
    "bulk_update",
    "bulk_patch",
    "bulk_delete",
]
type SchemaSetting[S] = type[S] | UndefinedType | None


class Page[R](BaseSchema):
    # Build schemas when item types are concrete, not unresolved CRUD type variables.
    model_config: ClassVar[ConfigDict] = ConfigDict(defer_build=True)

    items: list[R]
    total: Annotated[int, PydanticField(ge=0)]
    offset: Annotated[int, PydanticField(ge=0)] = 0
    limit: Annotated[int | None, PydanticField(ge=0)] = None
