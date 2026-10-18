from typing import overload

from typing_extensions import TypeVar

from fastsprout.core import (
    Depends,
    IdentificatorType,
    Schema,
)
from fastsprout.core.dto.conversion import (
    prepare_create,
    project_read,
    writable_names,
)
from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.types import AnyIterable
from fastsprout.core.types.protocols.identificable import Identificatable
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR
from fastsprout.data.streams.implementation.base_common_stream import (
    BaseCommonStream,
)
from fastsprout.data.types import Valuable
from fastsprout.data.utils.iterable import achain

from ..protocols.owners import (
    CreateOwner,
    EntityOwner,
    PatchOwner,
    QueryOwner,
    UpdateOwner,
)
from . import queries
from .batches import batch_count, batch_stream
from .payloads import (
    find_entity,
    prepare_write,
)

__all__ = [
    "bulk_create",
    "bulk_delete",
    "bulk_patch",
    "bulk_update",
    "create",
    "delete",
    "delete_by_query",
    "patch",
    "update",
    "update_by_query",
]

E = TypeVar("E", bound=Entitieable)
R = TypeVar("R", bound=Valuable | Entitieable, default=E)
C = TypeVar("C", bound=Schema | Entitieable, default=E)
U = TypeVar("U", bound=Schema | Entitieable, default=E)
P = TypeVar("P", bound=Schema | Entitieable, default=E)


async def create(
    self: CreateOwner[E, R, C], entity: E | C, datar: DataR = Depends()
) -> R:
    payload = prepare_create(self.entity, self.create_schema, entity)
    created = await datar.ability(self.entity).create(payload)
    return project_read(created, self.read_schema)


@overload
async def update(
    self: UpdateOwner[E, R, U], entity: E, /, *, datar: DataR = Depends()
) -> R: ...


@overload
async def update(
    self: UpdateOwner[E, R, U],
    entity: IdentificatorType,
    data: E | U,
    /,
    *,
    datar: DataR = Depends(),
) -> R: ...


async def update(
    self: UpdateOwner[E, R, U],
    entity: E | IdentificatorType,
    data: E | U | None = None,
    /,
    *,
    datar: DataR = Depends(),
) -> R:
    if isinstance(entity, self.entity) and data is None:
        prepared = await prepare_write(
            self.entity, entity.id, entity, self.entity, datar
        )
    elif data is not None and isinstance(entity, Identificatable):
        prepared = await prepare_write(
            self.entity, entity, data, self.update_schema, datar
        )
    else:
        raise TypeError("Use update(entity) or update(identifier, payload)")
    updated = await datar.ability(self.entity).update(prepared)
    return project_read(updated, self.read_schema)


async def patch(
    self: PatchOwner[E, R, P],
    identifier: IdentificatorType,
    data: E | P,
    /,
    *,
    datar: DataR = Depends(),
) -> R:
    prepared = await prepare_write(
        self.entity,
        identifier,
        data,
        self.patch_schema,
        datar,
        partial=True,
    )
    updated = await datar.ability(self.entity).update(prepared)
    return project_read(updated, self.read_schema)


async def delete(
    self: EntityOwner[E, R],
    identifier: IdentificatorType,
    datar: DataR = Depends(),
) -> int:
    found = await find_entity(self.entity, identifier, datar)
    if found is None:
        return 0
    return await datar.ability(self.entity).delete(found)


@batch_stream
async def bulk_create(
    self: CreateOwner[E, R, C],
    entities: AnyIterable[E | C],
    /,
    *,
    datar: DataR = Depends(),
) -> list[R]:
    prepared = [
        prepare_create(self.entity, self.create_schema, entity)
        async for entity in achain(entities)
    ]
    created = await datar.ability(self.entity).bulk_create(prepared)
    return [project_read(entity, self.read_schema) for entity in created]


@overload
def bulk_update(
    self: UpdateOwner[E, R, U],
    entities: AnyIterable[E],
    /,
    *,
    datar: DataR = Depends(),
) -> BaseCommonStream[R]: ...


@overload
def bulk_update(
    self: UpdateOwner[E, R, U],
    entities: AnyIterable[tuple[IdentificatorType, E | U]],
    /,
    *,
    datar: DataR = Depends(),
) -> BaseCommonStream[R]: ...


@batch_stream
async def bulk_update(
    self: UpdateOwner[E, R, U],
    entities: AnyIterable[E | tuple[IdentificatorType, E | U]],
    /,
    *,
    datar: DataR = Depends(),
) -> list[R]:
    prepared: list[E] = []
    async for item in achain(entities):
        if isinstance(item, tuple):
            key, data = item
            entity = await prepare_write(
                self.entity, key, data, self.update_schema, datar
            )
        else:
            entity = await prepare_write(
                self.entity, item.id, item, self.entity, datar
            )
        prepared.append(entity)
    updated = await datar.ability(self.entity).bulk_update(prepared)
    by_id = {entity.id: entity for entity in updated}
    return [
        project_read(by_id[entity.id], self.read_schema) for entity in prepared
    ]


@batch_stream
async def bulk_patch(
    self: PatchOwner[E, R, P],
    entities: AnyIterable[tuple[IdentificatorType, E | P]],
    /,
    *,
    datar: DataR = Depends(),
) -> list[R]:
    prepared = [
        await prepare_write(
            self.entity, key, data, self.patch_schema, datar, partial=True
        )
        async for key, data in achain(entities)
    ]
    updated = await datar.ability(self.entity).bulk_update(prepared)
    by_id = {entity.id: entity for entity in updated}
    return [
        project_read(by_id[entity.id], self.read_schema) for entity in prepared
    ]


@batch_count
async def bulk_delete(
    self: EntityOwner[E, R],
    identifiers: AnyIterable[IdentificatorType],
    /,
    *,
    datar: DataR = Depends(),
) -> int:
    entities: list[E] = []
    async for key in achain(identifiers):
        found = await find_entity(self.entity, key, datar)
        if found is not None:
            entities.append(found)
    return await datar.ability(self.entity).bulk_delete(entities)


async def delete_by_query[E: Entitieable, R: Valuable | Entitieable, Statement](
    self: QueryOwner[E, R],
    query: BaseQuery[E, Statement],
    *,
    datar: DataR = Depends(),
) -> int:
    return await datar.ability(self.entity).delete_by_query(
        queries.validated(self, datar, query)
    )


async def update_by_query[
    E: Entitieable,
    R: Valuable | Entitieable,
    Statement,
    Value,
](
    self: QueryOwner[E, R],
    query: BaseQuery[E, Statement],
    /,
    *assignments: FieldAssignment[Value],
    datar: DataR = Depends(),
) -> int:
    if any(
        item.name not in writable_names(self.entity) for item in assignments
    ):
        raise AttributeError("Update field is not writable")
    return await datar.ability(self.entity).update_by_query(
        queries.validated(self, datar, query), *assignments
    )
