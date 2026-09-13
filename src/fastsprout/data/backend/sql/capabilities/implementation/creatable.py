from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Any

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.base import SQLBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.capabilities.protocols import Creatable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.data.utils.collect import collect

__all__ = ["SQLDataCreatable"]


class SQLDataCreatable[E: SQLEntity[Any]](Creatable[E], SQLBackend[E]):
    async def create(self, entity: E, /) -> E:
        return (await self.bulk_create([entity]))[0]

    async def bulk_create(self, entities: Sequence[E], /):
        return await collect(self.iter_bulk_create)(entities)

    async def _handle_before_start(
        self,
        entities: AnyIterable[E],
    ) -> AnyIterable[E]:
        return entities

    async def _handle_before_add(self, entities: Sequence[E]) -> Sequence[E]:
        return entities

    async def _handle_after_add(self, entities: Sequence[E]) -> None:
        return None

    async def _handle_after_complete(self) -> None:
        return None

    async def iter_bulk_create(  # pyright: ignore[reportIncompatibleMethodOverride]
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
                    chunk = await self._handle_before_add(chunk)
                    session.add_all(chunk)
                    await session.flush()
                    yield chunk
                    await self._handle_after_add(chunk)
        await self._handle_after_complete()
