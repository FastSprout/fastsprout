from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Any

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.capabilities.protocols import Creatable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.data.utils.collect import collect

__all__ = ["SQLCreatable"]


class SQLCreatable[E: SQLEntity[Any]](Creatable[E], SQLDataBackend):
    async def create(self, entity: E, /) -> E:
        return (await self.bulk_create([entity]))[0]

    async def bulk_create(self, entities: Sequence[E], /):
        return await collect(self.iter_bulk_create)(entities)

    async def iter_bulk_create(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]:
        async with self._get_session_factory() as session:
            stream = SimpleAsyncEntityStream(entities)
            async with self._session_transaction(session):
                async for chunk in stream.chunked():
                    session.add_all(chunk)
                    await session.flush()
                    async for item in SimpleAsyncEntityStream(chunk):
                        yield item
