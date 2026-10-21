from collections.abc import AsyncIterator, Sequence
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import and_, column, select, update, values
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql import Select

from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.helpers import get_primary_key
from fastsprout.data.backend.sql.predicates import native_conditions
from fastsprout.data.backend.sql.streams import SQLEntityStream
from fastsprout.data.capabilities.protocols import (
    Updatable,
    UpdatableByQueryable,
)
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.events import UpdateEvent
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from fastsprout.data.utils.collect import collect
from fastsprout.data.utils.iterable import resolve_any_iterable

__all__ = ["SQLUpdatable", "SQLUpdatableByQuery"]


class SQLUpdatable[E: SQLEntity[Any]](Updatable[E], SQLDataBackend):
    async def update(self, entity: E, /) -> E:
        """Update an existing entity with its configured ORM cascades."""
        async with self.transaction() as session:
            keys = tuple(
                getattr(entity, key) for key in get_primary_key(type(entity))
            )
            if await session.get(type(entity), keys) is None:
                raise LookupError(f"No {type(entity).__name__} with key {keys}")
            updated = await session.merge(entity)
            await session.flush()
            await self.publish_update(updated)
            return updated

    async def bulk_update(self, entities: AnyIterable[E], /) -> Sequence[E]:
        return await collect(self.iter_bulk_update)(entities)

    async def iter_bulk_update(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]:
        async with self.transaction() as session:
            stream = SimpleAsyncEntityStream(entities)
            async for chunk in stream.chunked():
                entity_cls = type(chunk[0])
                table = entity_cls.__table__
                mapper = class_mapper(entity_cls)
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
                    column(col.key, col.columns[0].type)
                    for col in mapper.column_attrs
                ]
                data_view = (
                    values(
                        *values_cols,
                        name=f"{self.__class__.__name__}_update_data_{uuid4().hex}",
                    )
                    .data([tuple(mapping.values()) for mapping in mappings])
                    .cte(nesting=True)
                    .select()
                    .subquery()
                )

                where_conditions = [
                    table.c[key] == getattr(data_view.c, key) for key in pk_keys
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
                    item = entity_cls.model_validate(
                        {
                            key: value
                            for key, value in row.items()
                            if isinstance(key, str)
                        }
                    )
                    await self.publish_update(item)
                    yield item

    async def publish_update(self, entity: E) -> None:
        if self.with_events:
            await self._publish_to_bus(
                UpdateEvent[type(entity)](entity=entity)  # type: ignore[misc,operator]  # Mypy cannot express the runtime entity type in this subscription.
            )


class SQLUpdatableByQuery[E: SQLEntity[Any]](
    UpdatableByQueryable[E, BaseQuery[E, Select[tuple[E]]]], SQLDataBackend
):
    async def update_by_query(
        self,
        query: BaseQuery[E, Select[tuple[E]]],
        /,
        *assignments: FieldAssignment[Any],
    ) -> int:
        if not assignments:
            return 0

        entity = query.entity
        pk: Mapped[Any] = entity.id.orm  # pyright: ignore[reportGeneralTypeIssues]
        selections = (
            resolve_any_iterable((query.build().with_only_columns(pk),))
            if native_conditions(query)
            else (
                select(pk).where(pk.in_([item.id for item in batch]))
                async for batch in SQLEntityStream(
                    query, self._signpost
                ).chunked()
            )
        )
        rowcount = 0
        async with self.transaction() as session:
            async for built_q_id in selections:
                result = await session.stream(
                    select(entity).from_statement(
                        update(entity.__table__)
                        .where(pk.in_(built_q_id))
                        .values(
                            {
                                cast(
                                    Mapped[Any], getattr(entity, field.name).orm
                                ): field.value
                                for field in assignments
                            }
                        )
                        .returning(entity.__table__)
                    ),
                    execution_options={
                        "yield_per": DEFAULT_ITERATION_CHUNK_SIZE,
                        "populate_existing": True,
                    },
                )
                async for chunk in result.scalars().partitions():
                    if self.with_events:
                        await self._publish_to_bus(
                            *(
                                UpdateEvent[type(item)](entity=item)  # type: ignore[misc,operator]  # Mypy cannot express the runtime entity type in this subscription.
                                for item in chunk
                            )
                        )
                    rowcount += len(chunk)
        return rowcount
