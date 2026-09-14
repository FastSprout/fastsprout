from collections.abc import AsyncIterator, Sequence
from typing import Any

from sqlalchemy.sql.selectable import Select

from fastsprout.data.backend.sql.base import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Iterable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE

__all__ = ["SQLIterable"]


class SQLIterable[E: SQLEntity[Any], Q: SQLQuery](
    Iterable[E, Q], SQLDataBackend
):
    async def iter(self, query: SQLQuery[E], /) -> AsyncIterator[E]:  # pyright: ignore[reportIncompatibleMethodOverride]
        built_q: Select[tuple[E]] = query._built_query
        async with self._get_session_factory() as session:
            result = await session.stream(
                built_q,
                execution_options={"yield_per": DEFAULT_ITERATION_CHUNK_SIZE},
            )
            async for item in result.scalars():
                yield item

    async def iter_per(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        query: SQLQuery[E],
        /,
        *,
        chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE,
    ) -> AsyncIterator[Sequence[E]]:
        built_q: Select[tuple[E]] = query._built_query
        async with self._get_session_factory() as session:
            for chunk in (
                (await session.execute(built_q))
                .scalars()
                .yield_per(chunk_size)
                .partitions(chunk_size)
            ):
                yield chunk
