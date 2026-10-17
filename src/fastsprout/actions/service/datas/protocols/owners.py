from typing import Annotated, Protocol

from annotated_types import Ge

from fastsprout.core.depends.invocation import DependencyOwner

from ..types import Page

__all__ = [
    "CreateOwner",
    "EntityOwner",
    "PageOwner",
    "PatchOwner",
    "QueryOwner",
    "UpdateOwner",
]


class QueryOwner[E, R](Protocol):
    entity: type[E]
    read_schema: type[R]


class PageOwner[E, R](QueryOwner[E, R], Protocol):
    page_schema: type[Page[R]]


class EntityOwner[E, R](QueryOwner[E, R], DependencyOwner, Protocol):
    chunk_size: Annotated[int, Ge(1)]


class CreateOwner[E, R, C](EntityOwner[E, R], Protocol):
    create_schema: type[C]


class UpdateOwner[E, R, U](EntityOwner[E, R], Protocol):
    update_schema: type[U]


class PatchOwner[E, R, P](EntityOwner[E, R], Protocol):
    patch_schema: type[P]
