from collections.abc import AsyncIterator, Sequence
from typing import Any, cast

from sqlalchemy import CursorResult, update

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SoftDeletableSQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import SoftDeletable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.data.utils.collect import collect

__all__ = ["SQLSoftDeletable"]


class SQLSoftDeletable[E: SoftDeletableSQLEntity[Any], Q: SQLQuery](
    SoftDeletable[E, Q], SQLDataBackend
):
    async def soft_delete(self, entity: E, /) -> None:
        await self.bulk_soft_delete([entity])

    async def bulk_soft_delete(self, entities: AnyIterable[E], /) -> None:
        async with self._get_session_factory() as session:
            stream = SimpleAsyncEntityStream(entities)
            async with self._session_transaction(session):
                async for chunk in stream.chunked():
                    table = type(chunk[0]).__table__
                    await session.execute(
                        update(table)
                        .where(table.c.id.in_([item.id for item in chunk]))
                        .values(remove=True)
                    )

    async def soft_delete_by_query(self, query: SQLQuery[E], /) -> int:
        entity: type[E] = query.entity
        table = entity.__table__
        built_q_id = query._built_query.with_only_columns(table.c.id).order_by(
            None
        )

        async with self._get_session_factory() as session:
            async with self._session_transaction(session):
                raw_result = await session.execute(
                    query._built_update.where(
                        table.c.id.in_(built_q_id)
                    ).values(remove=True)
                )
                return cast(CursorResult[Any], raw_result).rowcount

    async def restore(self, entity: E, /) -> E:
        return (await self.bulk_restore([entity]))[0]

    async def bulk_restore(self, entities: AnyIterable[E], /) -> Sequence[E]:
        return await collect(self.iter_bulk_restore)(entities)

    async def iter_bulk_restore(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, entities: AnyIterable[E], /
    ) -> AsyncIterator[E]:
        async with self._get_session_factory() as session:
            stream = SimpleAsyncEntityStream(entities)
            async with self._session_transaction(session):
                async for chunk in stream.chunked():
                    entity_cls = type(chunk[0])
                    table = entity_cls.__table__
                    stmt = (
                        update(table)
                        .where(table.c.id.in_([item.id for item in chunk]))
                        .values(remove=False)
                        .returning(table)
                    )
                    result = await session.execute(stmt)
                    for row in result.mappings():
                        yield entity_cls.model_validate(
                            {
                                key: value
                                for key, value in row.items()
                                if isinstance(key, str)
                            }
                        )
