from collections.abc import AsyncIterator, Sequence
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import CursorResult, and_, column, inspect, update, values
from sqlalchemy.orm.base import Mapped

from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.base import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.helpers import get_primary_key
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import (
    Updatable,
    UpdatableByQuery,
)
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.data.utils.collect import collect

__all__ = ["SQLUpdatable", "SQLUpdatableByQuery"]


class SQLUpdatable[E: SQLEntity[Any]](Updatable[E], SQLDataBackend):
    async def update(self, entity: E, /) -> E:
        return (await self.bulk_update([entity]))[0]

    async def bulk_update(self, entities: AnyIterable[E], /) -> Sequence[E]:
        return await collect(self.iter_bulk_update)(entities)

    async def iter_bulk_update(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]:
        async with self._get_session_factory() as session:
            stream = SimpleAsyncEntityStream(entities)
            async with self._session_transaction(session):
                async for chunk in stream.chunked():
                    entity_cls = type(chunk[0])
                    table = entity_cls.__table__
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

                    values_cols = [
                        column(col.key, col.type) for col in mapper.column_attrs
                    ]
                    data_view = values(
                        *values_cols,
                        name=f"{self.__class__.__name__}_update_data_{uuid4().hex}",
                    ).data(cast(Sequence[tuple[Any, ...]], mappings))

                    where_conditions = [
                        table.c[key] == getattr(data_view.c, key)
                        for key in pk_keys
                    ]

                    update_stmt = (
                        update(table)
                        .where(and_(*where_conditions))
                        .values(
                            {
                                col.key: getattr(data_view.c, col.key)
                                for col in mapper.column_attrs
                                if col.key not in pk_keys
                            }
                        )
                        .returning(table)
                    )

                    result = await session.execute(update_stmt)
                    for row in result.mappings():
                        yield entity_cls.model_validate(
                            {
                                key: value
                                for key, value in row.items()
                                if isinstance(key, str)
                            }
                        )


class SQLUpdatableByQuery[E: SQLEntity[Any], Q: SQLQuery[SQLEntity[Any]]](
    UpdatableByQuery[E, Q], SQLDataBackend
):
    async def update_by_query(
        self,
        query: SQLQuery[E],
        /,
        *assignments: FieldAssignment[Any],
    ) -> int:
        if not assignments:
            return 0

        entity = query.entity
        built_q = query._built_query
        pk: Mapped[Any] = entity.id.orm  # pyright: ignore[reportGeneralTypeIssues]
        built_q_id = built_q.with_only_columns(pk).order_by(None)

        async with self._get_session_factory() as session:
            async with self._session_transaction(session):
                raw_result = await session.execute(
                    query._built_update.where(pk.in_(built_q_id)).values(
                        {
                            cast(
                                Mapped[Any], getattr(entity, field.name).orm
                            ): field.value
                            for field in assignments
                        }
                    )
                )
                return cast(CursorResult[Any], raw_result).rowcount
