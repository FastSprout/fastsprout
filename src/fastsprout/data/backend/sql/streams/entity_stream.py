from collections.abc import AsyncIterator, Awaitable, Callable, Hashable
from contextlib import AbstractAsyncContextManager
from functools import partial
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute, aliased
from sqlalchemy.sql import ColumnElement, Select, Selectable
from sqlalchemy.sql.elements import KeyedColumnElement

from fastsprout.core import lazy_await
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.backend.implementation import BaseDataBackend
from fastsprout.data.backend.sql.data_backend import (
    SQLDataBackend,
    prepare_query,
)
from fastsprout.data.backend.sql.entity import SQLEntity, SQLSignpost
from fastsprout.data.capabilities.query import (
    And,
    BaseQuery,
    Expression,
    FieldPredicate,
)
from fastsprout.data.capabilities.query.predicate import evaluate
from fastsprout.data.entity import Entitieable, Signpostable
from fastsprout.data.streams.implementation import (
    JoinedStream,
    SimpleAsyncEntityStream,
)
from fastsprout.data.streams.protocols import (
    AsyncEntityStreamable,
    AsyncValueStreamable,
)
from fastsprout.data.types import (
    GetterCallable,
    HashableAndValuable,
    MapperCallable,
    PredicateCallable,
)

from ..predicates import compile_predicate, native_conditions
from .value_stream import SQLValueStream

__all__ = ["SQLEntityStream", "get_column"]


def get_column[E, T](
    getter: Callable[[E], T | Awaitable[T]], statement: Selectable
) -> ColumnElement[T] | None:
    if not isinstance(getter, FieldRef):
        return None
    column = getter.orm
    if isinstance(column, QueryableAttribute):
        column = column.__clause_element__()
    if isinstance(column, KeyedColumnElement):
        return statement.corresponding_column(column)
    return None


class SQLEntityStream[E: SQLEntity[Any]](
    SimpleAsyncEntityStream[E], AsyncEntityStreamable[E], SQLDataBackend
):
    """Entity stream backed by a SQLAlchemy `Select`.

    Operations that SQL can express are pushed down into the statement
    (take → LIMIT, drop → OFFSET, sort by field → ORDER BY, distinct,
    count, first, column projection via to_values). Everything else
    (Python predicates/mappers) falls back to the in-memory stream over
    a server-side cursor — rows are never fully buffered.
    """

    def __init__(
        self,
        stmt: Select[tuple[E]] | BaseQuery[E, Select[tuple[E]]],
        signpost: (
            SQLSignpost
            | Signpostable[AbstractAsyncContextManager[AsyncSession]]
        ),
        /,
    ) -> None:
        BaseDataBackend.__init__(self, signpost)
        self.query: BaseQuery[E, Select[tuple[E]]] | None = None
        if isinstance(stmt, BaseQuery):
            stmt, self.query = prepare_query(stmt, native_conditions(stmt))
        self.statement = stmt

    def clone(self, stmt: Select[tuple[E]]) -> "SQLEntityStream[E]":
        return SQLEntityStream(stmt, self._signpost)

    def __aiter__(self) -> AsyncIterator[E]:
        if self.query is None:
            return self.scalars(self.statement)
        condition: Expression[E] = And(*self.query.conditions)
        stream = (
            SimpleAsyncEntityStream(self.scalars(self.statement))
            .filter(lambda entity: evaluate(condition, entity))
            .drop(self.query.offset_value)
        )
        if isinstance(self.query.limit_value, int):
            stream = stream.take(self.query.limit_value)
        return aiter(stream)

    def join[F: Entitieable, Key: Hashable, LeftOrm, RightOrm](
        self,
        other: AsyncEntityStreamable[F],
        *,
        on: tuple[FieldRef[E, Key, LeftOrm], FieldRef[F, Key, RightOrm]],
    ) -> JoinedStream[E, F]:
        if (
            not isinstance(other, SQLEntityStream)
            or self._signpost is not other._signpost
            or self.query is not None
            or other.query is not None
        ):
            return super().join(other, on=on)
        left_field, right_field = on
        left_select = self.statement.subquery()
        right_select = other.statement.subquery()
        left = aliased(left_field.entity_cls, left_select)
        right = aliased(right_field.entity_cls, right_select)
        left_column = left_select.c[left_field.name]
        right_column = right_select.c[right_field.name]
        statement = select(left, right).join(
            right,
            or_(
                left_column == right_column,
                left_column.is_(None) & right_column.is_(None),
            ),
        )

        return JoinedStream.from_factory(partial(self.rows, statement))

    def take(self, n: int) -> SimpleAsyncEntityStream[E]:
        if self.query is not None:
            return super().take(n)
        return self.clone(self.statement.limit(n))

    def drop(self, n: int) -> SimpleAsyncEntityStream[E]:
        if self.query is not None:
            return super().drop(n)
        return self.clone(self.statement.offset(n))

    def distinct(self) -> SimpleAsyncEntityStream[E]:
        if self.query is not None:
            return super().distinct()
        return self.clone(self.statement.distinct())

    def filter(
        self, predicate: PredicateCallable[E]
    ) -> SimpleAsyncEntityStream[E]:
        unpaged = self.statement.compare(
            self.statement.limit(None).offset(None)
        )
        if (
            self.query is None
            and unpaged
            and isinstance(predicate, FieldPredicate)
        ):
            condition = compile_predicate(
                predicate,
                self.statement.column_descriptions[0]["entity"],
                lambda name: self.statement.selected_columns[name],
            )
            if condition is not None:
                return self.clone(self.statement.where(condition))
        return SimpleAsyncEntityStream(self).filter(predicate)

    def sort[R: RichComparisonable[Any]](  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        key: GetterCallable[E, R],
        reverse: bool = False,
    ) -> AsyncEntityStreamable[E]:
        column = (
            None if self.query is not None else get_column(key, self.statement)
        )
        if column is None:
            return SimpleAsyncEntityStream(self).sort(key, reverse=reverse)
        return self.clone(
            self.statement.order_by(column.desc() if reverse else column.asc())
        )

    @lazy_await
    async def count(self) -> int:
        if self.query is not None:
            return await super().count()
        sub = self.statement.subquery()
        async with self.session() as session:
            result = await session.execute(
                select(func.count()).select_from(sub)
            )
            return int(result.scalar_one())

    @lazy_await
    async def first(self) -> E | None:
        if self.query is not None:
            return await super().first()
        async for item in self.clone(self.statement.limit(1)):
            return item
        return None

    def to_values[K: HashableAndValuable](  # pyright: ignore[reportIncompatibleMethodOverride]
        self, mapper: MapperCallable[E, K]
    ) -> AsyncValueStreamable[K]:
        sub = self.statement.subquery()
        column = None if self.query is not None else get_column(mapper, sub)
        if column is None:
            return SimpleAsyncEntityStream(self).to_values(mapper)
        return SQLValueStream(select(column).select_from(sub), self._signpost)
