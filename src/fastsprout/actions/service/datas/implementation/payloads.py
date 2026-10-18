"""Find entities and prepare update payloads through DataR."""

from fastsprout.core import IdentificatorType, Schema
from fastsprout.core.dto.conversion import prepare_update
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR

__all__ = ["find_entity", "prepare_write"]


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
    data: E | T,
    schema: type[T],
    datar: DataR,
    *,
    partial: bool = False,
) -> E:
    stored = await find_entity(source, key, datar)
    if stored is None:
        raise LookupError(f"No {source.__name__} with id {key}")
    return prepare_update(source, schema, data, stored, partial=partial)
