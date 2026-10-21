from typing import Annotated, Protocol

from annotated_types import Ge

from fastsprout.core.depends.invocation import DependencyOwnable

from ..types import Page

__all__ = [
    "CreateOwnable",
    "EntityOwnable",
    "PageOwnable",
    "PatchOwnable",
    "QueryOwnable",
    "UpdateOwnable",
]


class QueryOwnable[E, R](Protocol):
    entity: type[E]
    read_schema: type[R]


class PageOwnable[E, R](QueryOwnable[E, R], Protocol):
    page_schema: type[Page[R]]


class EntityOwnable[E, R](QueryOwnable[E, R], DependencyOwnable, Protocol):
    chunk_size: Annotated[int, Ge(1)]


class CreateOwnable[E, R, C](EntityOwnable[E, R], Protocol):
    create_schema: type[C]


class UpdateOwnable[E, R, U](EntityOwnable[E, R], Protocol):
    update_schema: type[U]


class PatchOwnable[E, R, P](EntityOwnable[E, R], Protocol):
    patch_schema: type[P]
