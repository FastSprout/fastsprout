from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Any

from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.base import SQLBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import (
    Updatable,
    UpdatableByQuery,
)
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.data.utils.collect import collect

__all__ = ["SQLUpdatable", "SQLUpdatableByQuery"]


class SQLUpdatable[E: SQLEntity[Any]](Updatable[E], SQLBackend[E]):
    async def update(self, entity: E, /) -> E:
        return (await self.bulk_update([entity]))[0]

    async def bulk_update(self, entities: AnyIterable[E], /) -> Sequence[E]:
        return await collect(self.iter_bulk_update)(entities)

    async def _handle_before_start(
        self,
        entities: AnyIterable[E],
    ) -> AnyIterable[E]:
        return entities

    async def _handle_before_update(self, entities: Sequence[E]) -> Sequence[E]:
        return entities

    async def _handle_after_update(self, entities: Sequence[E]) -> None:
        return None

    async def _handle_after_complete(self) -> None:
        return None

    async def iter_bulk_update(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        entities: AnyIterable[E],
        /,
        *,
        chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE,
    ) -> AsyncIterator[Sequence[E]]:
        entities = await self._handle_before_start(entities)
        async with self._get_session_factory() as session:
            stream = SimpleAsyncEntityStream(entities)
            async with self._session_transaction(session):
                async for chunk in stream.chunked(chunk_size):
                    chunk = await self._handle_before_update(chunk)
                    session.add_all(chunk)
                    await session.flush()
                    yield chunk
                    await self._handle_after_update(chunk)
        await self._handle_after_complete()


class SQLUpdatableByQuery[E: SQLEntity[Any], Q: SQLQuery](
    UpdatableByQuery[E, Q], SQLBackend[E]
):
    async def update_by_query(
        self,
        query: Q,
        /,
        *assignments: FieldAssignment[Any],
    ) -> int: ...
