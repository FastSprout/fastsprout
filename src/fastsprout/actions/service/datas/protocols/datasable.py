"""Structural contract for data services and their schema-specific actions."""

import builtins
from collections.abc import AsyncGenerator, Hashable, Sequence
from typing import Annotated, Protocol, overload

from annotated_types import Ge
from typing_extensions import TypeVar

from fastsprout.core import IdentificatorType, Schema, UndefinedType
from fastsprout.core.depends import DependsClass
from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.fields.field_predicate import FieldPredicate
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types import AnyIterable, LazyAwait
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR
from fastsprout.data.streams.protocols import (
    AsyncCommonStreamable,
)
from fastsprout.data.types import MapperCallable, Valuable

from ..types import DataSOperation, Page
from .owners import (
    CreateOwnable,
    EntityOwnable,
    PageOwnable,
    PatchOwnable,
    QueryOwnable,
    UpdateOwnable,
)

__all__ = ["DataSable"]

E = TypeVar("E", bound=Entitieable)
R = TypeVar("R", bound=Valuable | Entitieable, default=E)
C = TypeVar("C", bound=Schema | Entitieable, default=E)
U = TypeVar("U", bound=Schema | Entitieable, default=E)
P = TypeVar("P", bound=Schema | Entitieable, default=E)

CreateSetting = TypeVar(
    "CreateSetting",
    bound=UndefinedType | None,
    default=UndefinedType,
    covariant=True,
)


class DataSable(Protocol[E, R, C, U, P, CreateSetting]):
    entity: type[E]
    read_schema: type[R]
    create_schema: type[C]
    update_schema: type[U]
    patch_schema: type[P]
    page_schema: type[Page[R]]
    operations: frozenset[DataSOperation]
    dependencies: Sequence[DependsClass]
    chunk_size: Annotated[int, Ge(1)]

    async def create(
        self: "DataSable[E, R, C, U, P, UndefinedType]",
        entity: E | C,
        datar: DataR = ...,
    ) -> R: ...

    @overload
    async def update(
        self: UpdateOwnable[E, R, U], entity: E, /, *, datar: DataR = ...
    ) -> R: ...

    @overload
    async def update(
        self: UpdateOwnable[E, R, U],
        identifier: IdentificatorType,
        data: E | U,
        /,
        *,
        datar: DataR = ...,
    ) -> R: ...

    async def patch(
        self: PatchOwnable[E, R, P],
        identifier: IdentificatorType,
        data: E | P,
        /,
        *,
        datar: DataR = ...,
    ) -> R: ...

    async def delete(
        self: EntityOwnable[E, R],
        identifier: IdentificatorType,
        datar: DataR = ...,
    ) -> int: ...

    async def upsert(
        self: EntityOwnable[E, R], entity: E, datar: DataR = ...
    ) -> R: ...

    def bulk_create(
        self: CreateOwnable[E, R, C],
        entities: AnyIterable[E | C],
        /,
        *,
        datar: DataR = ...,
    ) -> AsyncCommonStreamable[R]: ...

    @overload
    def bulk_update(
        self: UpdateOwnable[E, R, U],
        entities: AnyIterable[E],
        /,
        *,
        datar: DataR = ...,
    ) -> AsyncCommonStreamable[R]: ...

    @overload
    def bulk_update(
        self: UpdateOwnable[E, R, U],
        entities: AnyIterable[tuple[IdentificatorType, E | U]],
        /,
        *,
        datar: DataR = ...,
    ) -> AsyncCommonStreamable[R]: ...

    def bulk_patch(
        self: PatchOwnable[E, R, P],
        entities: AnyIterable[tuple[IdentificatorType, E | P]],
        /,
        *,
        datar: DataR = ...,
    ) -> AsyncCommonStreamable[R]: ...

    def bulk_upsert(
        self: EntityOwnable[E, R],
        entities: AnyIterable[E],
        /,
        *,
        datar: DataR = ...,
    ) -> AsyncCommonStreamable[R]: ...

    def bulk_delete(
        self: EntityOwnable[E, R],
        identifiers: AnyIterable[IdentificatorType],
        /,
        *,
        datar: DataR = ...,
    ) -> LazyAwait[int]: ...

    @overload
    async def update_by_query[Statement, Value](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Statement],
        /,
        *assignments: FieldAssignment[Value],
        datar: DataR = ...,
    ) -> int: ...

    @overload
    async def update_by_query[Value](
        self: QueryOwnable[E, R],
        query: FieldPredicate[E],
        /,
        *assignments: FieldAssignment[Value] | FieldPredicate[E],
        datar: DataR = ...,
    ) -> int: ...

    @overload
    async def delete_by_query[Statement](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Statement],
        *,
        datar: DataR = ...,
    ) -> int: ...

    @overload
    async def delete_by_query(
        self: QueryOwnable[E, R],
        query: FieldPredicate[E],
        /,
        *predicates: FieldPredicate[E],
        datar: DataR = ...,
    ) -> int: ...

    async def get[Statement](
        self: QueryOwnable[E, R],
        identifier: IdentificatorType | BaseQuery[E, Statement],
        datar: DataR = ...,
    ) -> R | None: ...

    async def exists[Statement](
        self: QueryOwnable[E, R],
        identifier: IdentificatorType | BaseQuery[E, Statement],
        datar: DataR = ...,
    ) -> bool: ...

    async def count[Statement](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Statement] | None = ...,
        *,
        datar: DataR = ...,
    ) -> int: ...

    async def list[Statement](
        self: PageOwnable[E, R],
        query: BaseQuery[E, Statement] | None = ...,
        *,
        datar: DataR = ...,
    ) -> Page[R]: ...

    async def find_first[Statement](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Statement],
        *,
        datar: DataR = ...,
    ) -> R | None: ...

    async def find_exactly_one[Statement](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Statement] | FieldPredicate[E],
        *predicates: FieldPredicate[E],
        datar: DataR = ...,
    ) -> R: ...

    async def find_all[Statement](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Statement],
        *,
        datar: DataR = ...,
    ) -> builtins.list[R]: ...

    @overload
    def stream[Statement](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Statement],
        *,
        datar: DataR = ...,
    ) -> AsyncCommonStreamable[R]: ...

    @overload
    def stream(
        self: QueryOwnable[E, R],
        query: FieldPredicate[E],
        /,
        *predicates: FieldPredicate[E],
        datar: DataR = ...,
    ) -> AsyncCommonStreamable[R]: ...

    def map[O: Schema, Statement](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Statement],
        mapper: MapperCallable[R, O],
        *,
        datar: DataR = ...,
    ) -> AsyncGenerator[O, None]: ...

    def join[
        Other: Entitieable,
        Left,
        Right,
        Key: Hashable,
        LeftOrm,
        RightOrm,
    ](
        self: QueryOwnable[E, R],
        query: BaseQuery[E, Left],
        other: BaseQuery[Other, Right],
        *,
        on: tuple[FieldRef[E, Key, LeftOrm], FieldRef[Other, Key, RightOrm]],
        datar: DataR = ...,
    ) -> AsyncGenerator[tuple[R, Other], None]: ...
