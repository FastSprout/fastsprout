from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from fastsprout.core import lazy_await
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.backend.implementation import BaseDataBackend
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLSignpost
from fastsprout.data.entity import Signpostable
from fastsprout.data.streams.implementation import SimpleAsyncValueStream
from fastsprout.data.streams.implementation.base_common_stream import (
    BaseCommonStream,
)
from fastsprout.data.streams.protocols import AsyncValueStream
from fastsprout.data.types import (
    GetterCallable,
    Valuable,
)

__all__ = ["SQLValueStream"]


class SQLValueStream[T: Valuable](
    SimpleAsyncValueStream[T], AsyncValueStream[T], SQLDataBackend
):
    """Single-column stream backed by a SQLAlchemy `Select`.

    Pushes down take/drop/distinct/sort and the aggregate terminals
    (count, sum, min, max) into SQL; Python callables fall back to the
    in-memory stream over a server-side cursor.
    """

    def __init__(
        self,
        stmt: Select[tuple[T]],
        signpost: (
            SQLSignpost
            | Signpostable[AbstractAsyncContextManager[AsyncSession]]
        ),
        /,
    ) -> None:
        BaseDataBackend.__init__(self, signpost)
        self._stmt = stmt

    def _clone(self, stmt: Select[tuple[T]]) -> "SQLValueStream[T]":
        return SQLValueStream(stmt, self._signpost)

    def __aiter__(self) -> AsyncIterator[T]:
        async def gen() -> AsyncIterator[T]:
            async with self.session() as session:
                result = await session.stream(self._stmt)
                async for item in result.scalars():
                    self._check_stream_context()
                    yield item

        return gen()

    async def _aggregate(self, fn: Any) -> Any:
        sub = self._stmt.subquery()
        column = next(iter(sub.c))
        async with self.session() as session:
            result = await session.execute(select(fn(column)))
            return result.scalar_one()

    def take(self, n: int) -> "SQLValueStream[T]":
        return self._clone(self._stmt.limit(n))

    def drop(self, n: int) -> "SQLValueStream[T]":
        return self._clone(self._stmt.offset(n))

    def distinct(self) -> "SQLValueStream[T]":
        return self._clone(self._stmt.distinct())

    def sort[R: RichComparisonable](  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        key: GetterCallable[T, R] | None = None,
        reverse: bool = False,
    ) -> AsyncValueStream[T]:
        if key is not None:
            return cast(
                AsyncValueStream[T],
                SimpleAsyncValueStream(self).sort(key, reverse=reverse),
            )
        sub = self._stmt.subquery()
        column = next(iter(sub.c))
        order = column.desc() if reverse else column.asc()
        return self._clone(select(column).select_from(sub).order_by(order))

    @lazy_await
    async def count(self) -> int:
        sub = self._stmt.subquery()
        async with self.session() as session:
            result = await session.execute(
                select(func.count()).select_from(sub)
            )
            return int(result.scalar_one())

    @lazy_await
    async def first(self) -> T | None:
        async for item in self._clone(self._stmt.limit(1)):
            return item
        return None

    @lazy_await
    async def sum(self) -> T | None:
        return await self._aggregate(func.sum)

    @lazy_await
    async def min[K: RichComparisonable](  # pyright: ignore[reportIncompatibleMethodOverride]
        self, key: GetterCallable[T, K] | None = None
    ) -> T | None:
        if key is not None:
            return await BaseCommonStream.min(self, key)
        return await self._aggregate(func.min)

    @lazy_await
    async def max[K: RichComparisonable](  # pyright: ignore[reportIncompatibleMethodOverride]
        self, key: GetterCallable[T, K] | None = None
    ) -> T | None:
        if key is not None:
            return await BaseCommonStream.max(self, key)
        return await self._aggregate(func.max)
