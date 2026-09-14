from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.sql import Select
from sqlmodel import Column

from fastsprout.core import lazy_await
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.session import SessionFactory
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.streams.implementation import (
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
)

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
    SimpleAsyncEntityStream[E], AsyncEntityStream[E]
):
    """Entity stream backed by a SQLAlchemy `Select`.

    Operations that SQL can express are pushed down into the statement
    (take → LIMIT, drop → OFFSET, sort by field → ORDER BY, distinct,
    count, first, column projection via to_values). Everything else
    (Python predicates/mappers) falls back to the in-memory stream over
    a server-side cursor — rows are never fully buffered.
    """

    def __init__(
        self, stmt: Select[tuple[E]], session_factory: SessionFactory
    ) -> None:
        self._stmt = stmt
        self._session_factory = session_factory

    def _clone(self, stmt: Select[tuple[E]]) -> "SQLEntityStream[E]":
        return SQLEntityStream(stmt, self._session_factory)

    def __aiter__(self) -> AsyncIterator[E]:
        async def gen() -> AsyncIterator[E]:
            async with self._session_factory() as session:
                result = await session.stream(
                    self._stmt,
                    execution_options={
                        "yield_per": DEFAULT_ITERATION_CHUNK_SIZE
                    },
                )
                async for item in result.scalars():
                    yield item

        return gen()

    def take(self, n: int) -> "SQLEntityStream[E]":
        return self._clone(self._stmt.limit(n))

    def drop(self, n: int) -> "SQLEntityStream[E]":
        return self._clone(self._stmt.offset(n))

    def distinct(self) -> "SQLEntityStream[E]":
        return self._clone(self._stmt.distinct())

    def sort[R: RichComparisonable[Any]](  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        key: GetterCallable[E, R],
        reverse: bool = False,
    ) -> AsyncEntityStream[E]:
        orm = _orm_of(key)  # pyright: ignore[reportArgumentType]
        if orm is None:
            return SimpleAsyncEntityStream(self).sort(key, reverse=reverse)
        return self._clone(
            self._stmt.order_by(orm.desc() if reverse else orm.asc())
        )

    @lazy_await
    async def count(self) -> int:
        sub = self._stmt.subquery()
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(sub)
            )
            return int(result.scalar_one())

    @lazy_await
    async def first(self) -> E | None:
        async for item in self._clone(self._stmt.limit(1)):
            return item
        return None

    def to_values[K: HashableAndValuable](  # pyright: ignore[reportIncompatibleMethodOverride]
        self, mapper: MapperCallable[E, K]
    ) -> AsyncValueStream[K]:
        orm = _orm_of(mapper)  # pyright: ignore[reportArgumentType]
        if orm is None:
            return SimpleAsyncEntityStream(self).to_values(mapper)
        sub = self._stmt.subquery()
        return SQLValueStream(
            select(sub.c[orm.key]).select_from(sub), self._session_factory
        )
