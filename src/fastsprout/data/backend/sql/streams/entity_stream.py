from collections.abc import AsyncGenerator, AsyncIterator, Hashable
from contextlib import AbstractAsyncContextManager
from functools import partial
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import Select
from sqlmodel import Column

from fastsprout.core import lazy_await
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.backend.implementation import BaseDataBackend
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity, SQLSignpost
from fastsprout.data.capabilities.query import And, FieldPredicate
from fastsprout.data.capabilities.query.predicate import evaluate
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import Entitieable, Signpostable
from fastsprout.data.streams.implementation import (
    JoinedStream,
    SimpleAsyncEntityStream,
)
from fastsprout.data.streams.protocols import (
    AsyncEntityStream,
    AsyncValueStream,
)
from fastsprout.data.types import (
    GetterCallable,
    HashableAndValuable,
    MapperCallable,
    PredicateCallable,
)

from ..query import SQLQuery, compile_predicate
from .value_stream import SQLValueStream

__all__ = ["SQLEntityStream"]


def _orm_of[T: HashableAndValuable](
    getter: FieldRef[SQLEntity[Any], T, Column[T | Any]],
) -> Column[T] | None:
    """SQL-expressible column for a getter, or None for Python callables.

    Class-level field access (`Hero.name`) yields a FieldRef carrying the
    mapped attribute; arbitrary lambdas cannot be pushed down to SQL.
    """
    return getter.orm if isinstance(getter, FieldRef) else None


class SQLEntityStream[E: SQLEntity[Any]](
    SimpleAsyncEntityStream[E], AsyncEntityStream[E], SQLDataBackend
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
        stmt: Select[tuple[E]] | SQLQuery[E],
        signpost: (
            SQLSignpost
            | Signpostable[AbstractAsyncContextManager[AsyncSession]]
        ),
        /,
    ) -> None:
        BaseDataBackend.__init__(self, signpost)
        self.query: SQLQuery[E] | None = None
        if isinstance(stmt, SQLQuery):
            if not stmt.native_conditions:
                self.query = stmt.copy()
                stmt = stmt.unpaged()
                stmt.conditions = ()
            stmt = stmt.build()
        self._stmt = stmt

    def _clone(self, stmt: Select[tuple[E]]) -> "SQLEntityStream[E]":
        return SQLEntityStream(stmt, self._signpost)

    def __aiter__(self) -> AsyncIterator[E]:
        if self.query is None:
            return self.scalars(self._stmt)
        stream = (
            SimpleAsyncEntityStream(self.scalars(self._stmt))
            .filter(partial(evaluate, And(*self.query.conditions)))
            .drop(self.query.offset_value)
        )
        if isinstance(self.query.limit_value, int):
            stream = stream.take(self.query.limit_value)
        return aiter(stream)

    def join[F: Entitieable, Key: Hashable, LeftOrm, RightOrm](
        self,
        other: AsyncEntityStream[F],
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
        left_select = self._stmt.subquery()
        right_select = other._stmt.subquery()
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

        async def rows() -> AsyncGenerator[tuple[E, F], None]:
            async with self.session() as session:
                result = await session.stream(
                    statement,
                    execution_options={
                        "yield_per": DEFAULT_ITERATION_CHUNK_SIZE
                    },
                )
                try:
                    async for row in result.tuples():
                        self._check_stream_context()
                        yield row
                finally:
                    await result.close()

        return JoinedStream.from_factory(rows)

    def take(self, n: int) -> SimpleAsyncEntityStream[E]:
        if self.query is not None:
            return super().take(n)
        return self._clone(self._stmt.limit(n))

    def drop(self, n: int) -> SimpleAsyncEntityStream[E]:
        if self.query is not None:
            return super().drop(n)
        return self._clone(self._stmt.offset(n))

    def distinct(self) -> SimpleAsyncEntityStream[E]:
        if self.query is not None:
            return super().distinct()
        return self._clone(self._stmt.distinct())

    def filter(
        self, predicate: PredicateCallable[E]
    ) -> SimpleAsyncEntityStream[E]:
        unpaged = self._stmt.compare(self._stmt.limit(None).offset(None))
        if (
            self.query is None
            and unpaged
            and isinstance(predicate, FieldPredicate)
        ):
            condition = compile_predicate(
                predicate,
                self._stmt.column_descriptions[0]["entity"],
                lambda name: self._stmt.selected_columns[name],
            )
            if condition is not None:
                return self._clone(self._stmt.where(condition))
        return SimpleAsyncEntityStream(self).filter(predicate)

    def sort[R: RichComparisonable[Any]](  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        key: GetterCallable[E, R],
        reverse: bool = False,
    ) -> AsyncEntityStream[E]:
        orm = _orm_of(key)  # pyright: ignore[reportArgumentType]
        if self.query is not None or orm is None:
            return SimpleAsyncEntityStream(self).sort(key, reverse=reverse)
        return self._clone(
            self._stmt.order_by(orm.desc() if reverse else orm.asc())
        )

    @lazy_await
    async def count(self) -> int:
        if self.query is not None:
            return await super().count()
        sub = self._stmt.subquery()
        async with self.session() as session:
            result = await session.execute(
                select(func.count()).select_from(sub)
            )
            return int(result.scalar_one())

    @lazy_await
    async def first(self) -> E | None:
        if self.query is not None:
            return await super().first()
        async for item in self._clone(self._stmt.limit(1)):
            return item
        return None

    def to_values[K: HashableAndValuable](  # pyright: ignore[reportIncompatibleMethodOverride]
        self, mapper: MapperCallable[E, K]
    ) -> AsyncValueStream[K]:
        orm = _orm_of(mapper)  # pyright: ignore[reportArgumentType]
        if self.query is not None or orm is None:
            return SimpleAsyncEntityStream(self).to_values(mapper)
        sub = self._stmt.subquery()
        return SQLValueStream(
            select(sub.c[orm.key]).select_from(sub), self._signpost
        )
