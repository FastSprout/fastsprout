"""Prepare CRUD payloads and resolve related entities through DataR."""

from fastsprout.core import IdentificatorType, ReadDTO, Schema
from fastsprout.core.dto.conversion import (
    field_names,
    prepare_create,
    prepare_update,
    writable_names,
)
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR

__all__ = [
    "find_entity",
    "materialize",
    "prepare_new_entity",
    "prepare_upsert",
    "prepare_write",
]


async def prepare_new_entity[E: Entitieable, C: Schema | Entitieable](
    source: type[E],
    schema: type[C],
    entity: C,
    datar: DataR,
    *,
    relations: dict[int, Entitieable[IdentificatorType]] | None = None,
) -> E:
    payload: E = prepare_create(source, schema, entity)
    return await materialize(
        source, payload, datar, creating=True, relations=relations
    )


async def find_entity[E: Entitieable](
    source: type[E], key: IdentificatorType, datar: DataR
) -> E | None:
    ability = datar.ability(source)
    return await ability.find_first(
        ability.query_for(source).where(source.id.eq(key))
    )


async def prepare_write[E: Entitieable, T: Schema | Entitieable](
    source: type[E],
    key: IdentificatorType,
    data: T,
    schema: type[T],
    datar: DataR,
    *,
    partial: bool = False,
) -> E:
    stored = await require_entity(source, key, datar)
    payload: E = prepare_update(source, schema, data, stored, partial=partial)
    return await materialize(
        source, payload, datar, creating=False, stored=stored
    )


async def require_entity[E: Entitieable](
    source: type[E], key: IdentificatorType, datar: DataR
) -> E:
    entity = await find_entity(source, key, datar)
    if entity is None:
        raise LookupError(f"No {source.__name__} with id {key}")
    return entity


async def materialize[E: Entitieable](
    source: type[E],
    entity: E,
    datar: DataR,
    *,
    creating: bool,
    ancestors: tuple[int, ...] = (),
    stored: E | None = None,
    relations: dict[int, Entitieable[IdentificatorType]] | None = None,
) -> E:
    if id(entity) in ancestors:
        raise ValueError("Cyclic CRUD payload")
    ancestors = (*ancestors, id(entity))
    relations = {} if relations is None else relations
    if creating:
        values = dict(vars(entity))
    else:
        stored = (
            stored
            if stored is not None
            else await require_entity(source, entity.id, datar)
        )
        values = vars(stored) | {
            name: getattr(entity, name)
            for name in writable_names(source) & vars(entity).keys()
        }
    for name, value in tuple(values.items()):
        if not isinstance(value, Entitieable):
            continue
        values[name] = await materialize_relation(
            value,
            datar,
            creating=creating,
            ancestors=ancestors,
            relations=relations,
        )
    return source(
        **{
            name: value
            for name, value in values.items()
            if not name.startswith("_")
        }
    )


async def materialize_relation(
    entity: Entitieable[IdentificatorType],
    datar: DataR,
    *,
    creating: bool,
    ancestors: tuple[int, ...],
    relations: dict[int, Entitieable[IdentificatorType]],
) -> Entitieable[IdentificatorType]:
    if id(entity) in relations:
        return relations[id(entity)]
    source: type[Entitieable[IdentificatorType]] = (
        entity.__fastsprout_source__
        if isinstance(entity, ReadDTO)
        else type(entity)
    )
    if creating and isinstance(entity, ReadDTO):
        return await require_entity(source, entity.id, datar)
    if creating and "id" in field_names(type(entity), "read"):
        stored = await find_entity(source, entity.id, datar)
        if stored is not None:
            return stored
    payload: Entitieable[IdentificatorType] = (
        prepare_create(source, source, entity) if creating else entity
    )
    result = await materialize(
        source,
        payload,
        datar,
        creating=creating,
        ancestors=ancestors,
        relations=relations,
    )
    relations[id(entity)] = result
    return result


async def prepare_upsert[E: Entitieable](
    source: type[E], entity: E, datar: DataR
) -> E:
    found = await find_entity(source, entity.id, datar)
    return await materialize(source, entity, datar, creating=found is None)
