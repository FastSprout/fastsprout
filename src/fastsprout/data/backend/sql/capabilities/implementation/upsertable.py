from collections.abc import AsyncIterator, Sequence
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.base import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.helpers import get_primary_key
from fastsprout.data.capabilities.protocols import Updatable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.data.utils.collect import collect

__all__ = ["SQLUpsertable"]


class SQLUpsertable[E: SQLEntity[Any]](Updatable[E], SQLDataBackend):
    async def upsert(self, entity: E, /) -> E:
        return (await self.bulk_upsert([entity]))[0]

    async def bulk_upsert(self, entities: AnyIterable[E], /) -> Sequence[E]:
        return await collect(self.iter_bulk_upsert)(entities)

    async def iter_bulk_upsert(
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]:
        async with self._get_session_factory() as session:
            stream = SimpleAsyncEntityStream(entities)
            async with self._session_transaction(session):
                async for chunk in stream.chunked():
                    entity_cls = type(chunk[0])
                    mapper = inspect(entity_cls)
                    pk_keys = get_primary_key(entity_cls)

                    mappings = [
                        {
                            col.key: getattr(item, col.key)
                            for col in mapper.column_attrs
                        }
                        for item in chunk
                    ]

                    if not mappings:
                        continue

                    stmt = insert(entity_cls).values(mappings)

                    update_cols = {
                        col.key: stmt.excluded[col.key]
                        for col in mapper.column_attrs
                        if col.key not in pk_keys
                    }

                    upsert_stmt = stmt.on_conflict_do_update(
                        index_elements=list(mapper.primary_key),
                        set_=update_cols,
                    ).returning(entity_cls)

                    result = await session.stream(
                        upsert_stmt,
                        execution_options={"populate_existing": True},
                    )
                    async for item in result.scalars():
                        yield item
