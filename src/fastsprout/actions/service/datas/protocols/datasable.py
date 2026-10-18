"""Structural contract for data services and their schema-specific actions."""

import builtins
from collections.abc import AsyncGenerator, Callable, Sequence
from typing import Annotated, Protocol, overload

from annotated_types import Ge
from typing_extensions import TypeVar

from fastsprout.core import IdentificatorType, Schema, WriteDTO
from fastsprout.core.depends import DependsClass
from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.types import AnyIterable, LazyAwait
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR
from fastsprout.data.streams.protocols import (
    AsyncCommonStream,
    AsyncEntityStream,
)
from fastsprout.data.types import Valuable

from ..types import DataSOperation, Page

__all__ = ["DataSable"]

E = TypeVar("E", bound=Entitieable)
R = TypeVar("R", bound=Valuable | Entitieable, default=E)
C = TypeVar("C", bound=Schema, default=WriteDTO)
U = TypeVar("U", bound=Schema, default=WriteDTO)
P = TypeVar("P", bound=Schema, default=WriteDTO)


class DataSable(Protocol[E, R, C, U, P]):
    entity: type[E]
    read_schema: type[R]
    create_schema: type[C]
    update_schema: type[U]
    patch_schema: type[P]
    page_schema: type[Page[R]]
    operations: frozenset[DataSOperation]
    dependencies: Sequence[DependsClass]
    chunk_size: Annotated[int, Ge(1)]

    async def create(self, entity: E | C, datar: DataR = ...) -> R: ...

    @overload
    async def update(self, entity: E, /, *, datar: DataR = ...) -> R: ...

    @overload
    async def update(
        self,
        identifier: IdentificatorType,
        data: E | U,
        /,
        *,
        datar: DataR = ...,
    ) -> R: ...

    async def patch(
        self,
        identifier: IdentificatorType,
        data: E | P,
        /,
        *,
        datar: DataR = ...,
    ) -> R: ...

    async def delete(
        self, identifier: IdentificatorType, datar: DataR = ...
    ) -> int: ...

    async def upsert(self, entity: E, datar: DataR = ...) -> R: ...

    def bulk_create(
        self, entities: AnyIterable[E | C], /, *, datar: DataR = ...
    ) -> AsyncCommonStream[R]: ...

    @overload
    def bulk_update(
        self, entities: AnyIterable[E], /, *, datar: DataR = ...
    ) -> AsyncCommonStream[R]: ...

    @overload
    def bulk_update(
        self,
        entities: AnyIterable[tuple[IdentificatorType, E | U]],
        /,
        *,
        datar: DataR = ...,
    ) -> AsyncCommonStream[R]: ...

    def bulk_patch(
        self,
        entities: AnyIterable[tuple[IdentificatorType, E | P]],
        /,
        *,
        datar: DataR = ...,
    ) -> AsyncCommonStream[R]: ...

    def bulk_upsert(
        self, entities: AnyIterable[E], /, *, datar: DataR = ...
    ) -> AsyncCommonStream[R]: ...

    def bulk_delete(
        self,
        identifiers: AnyIterable[IdentificatorType],
        /,
        *,
        datar: DataR = ...,
    ) -> LazyAwait[int]: ...

    async def update_by_query[Statement, Value](
        self,
        query: BaseQuery[E, Statement],
        /,
        *assignments: FieldAssignment[Value],
        datar: DataR = ...,
    ) -> int: ...

    async def delete_by_query[Statement](
        self, query: BaseQuery[E, Statement], *, datar: DataR = ...
    ) -> int: ...

    async def get[Statement](
        self,
        identifier: IdentificatorType | BaseQuery[E, Statement],
        datar: DataR = ...,
    ) -> R | None: ...

    async def exists[Statement](
        self,
        identifier: IdentificatorType | BaseQuery[E, Statement],
        datar: DataR = ...,
    ) -> bool: ...

    def stream[Statement](
        self, datar: DataR, query: BaseQuery[E, Statement] | None
    ) -> AsyncEntityStream[E]: ...

    async def count[Statement](
        self,
        query: BaseQuery[E, Statement] | None = ...,
        *,
        datar: DataR = ...,
    ) -> int: ...

    async def list[Statement](
        self,
        query: BaseQuery[E, Statement] | None = ...,
        *,
        datar: DataR = ...,
    ) -> Page[R]: ...

    async def find_first[Statement](
        self, query: BaseQuery[E, Statement], *, datar: DataR = ...
    ) -> R | None: ...

    async def find_exactly_one[Statement](
        self, query: BaseQuery[E, Statement], *, datar: DataR = ...
    ) -> R: ...

    async def find_all[Statement](
        self, query: BaseQuery[E, Statement], *, datar: DataR = ...
    ) -> builtins.list[R]: ...

    def iter[Statement](
        self, query: BaseQuery[E, Statement], *, datar: DataR = ...
    ) -> AsyncCommonStream[R]: ...

    def project[O: Schema, Statement](
        self,
        query: BaseQuery[E, Statement],
        mapper: Callable[[R], O],
        *,
        datar: DataR = ...,
    ) -> AsyncGenerator[O, None]: ...
