from collections.abc import AsyncIterator, Sequence
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.helpers import get_primary_key
from fastsprout.data.capabilities.protocols import Upsertable
from fastsprout.data.events import CreateEvent, UpdateEvent
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.data.utils.collect import collect

__all__ = ["SQLUpsertable"]


class SQLUpsertable[E: SQLEntity[Any]](Upsertable[E], SQLDataBackend):
    async def upsert(self, entity: E, /) -> E:
        return (await self.bulk_upsert([entity]))[0]

    async def bulk_upsert(self, entities: AnyIterable[E], /) -> Sequence[E]:
        return await collect(self.iter_bulk_upsert)(entities)

    async def iter_bulk_upsert(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: C901
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]:
        async with self.transaction() as session:
            stream = SimpleAsyncEntityStream(entities)
            async for chunk in stream.chunked():
                entity_cls = type(chunk[0])
                mapper = inspect(entity_cls)
                pk_keys = get_primary_key(entity_cls)
                pk: Mapped[Any] = entity_cls.id.orm  # pyright: ignore[reportGeneralTypeIssues]
                built_q_id = (
                    self.query_for(entity_cls)
                    ._built_select.with_only_columns(pk)
                    .order_by(None)
                )

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

                exists_pks = set()
                if self.with_events:
                    exists_pks = set(
                        x[0]
                        for x in (await session.execute(built_q_id)).fetchall()
                    )

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
                    if self.with_events:
                        if item.id in exists_pks:
                            await self._publish_to_bus(
                                UpdateEvent[type(item)](entity=item)  # type: ignore[misc,operator]
                            )
                        else:
                            await self._publish_to_bus(
                                CreateEvent[type(item)](entity=item)  # type: ignore[misc,operator]
                            )
