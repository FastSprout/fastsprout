from typing import Any, cast

from sqlalchemy import CursorResult, delete

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Deletable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream

__all__ = ["SQLDeletable"]


class SQLDeletable[E: SQLEntity[Any], Q: SQLQuery](
    Deletable[E, Q], SQLDataBackend
):
    async def delete(self, entity: E, /) -> int:
        return await self.bulk_delete([entity])

    async def bulk_delete(self, entities: AnyIterable[E], /) -> int:
        deleted = 0
        async with self._get_session_factory() as session:
            stream = SimpleAsyncEntityStream(entities)
            async with self._session_transaction(session):
                async for chunk in stream.chunked():
                    table = type(chunk[0]).__table__
                    stmt = delete(table).where(
                        table.c.id.in_([item.id for item in chunk])
                    )
                    result = await session.execute(stmt)
                    deleted += cast(CursorResult[Any], result).rowcount
        return deleted

    async def delete_by_query(self, query: SQLQuery[E], /) -> int:
        entity = query.entity
        built_q_id = query._built_query.with_only_columns(
            entity.__table__.c.id
        ).order_by(None)

        async with self._get_session_factory() as session:
            async with self._session_transaction(session):
                raw_result = await session.execute(
                    query._built_delete.where(
                        entity.__table__.c.id.in_(built_q_id)
                    )
                )
                return cast(CursorResult[Any], raw_result).rowcount
