from typing import overload

from typing_extensions import TypeVar

from fastsprout.core import (
    Depends,
    IdentificatorType,
    Schema,
)
from fastsprout.core.dto.conversion import prepare_create, project_read
from fastsprout.core.types.protocols.identificable import Identificatable
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR
from fastsprout.data.types import Valuable

from ..protocols.owners import (
    CreateOwner,
    EntityOwner,
    PatchOwner,
    UpdateOwner,
)
from .payloads import (
    find_entity,
    prepare_write,
)

__all__ = ["create", "delete", "patch", "update"]

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
