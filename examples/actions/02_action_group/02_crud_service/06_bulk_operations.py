"""Create, update, patch, and delete batches from single-use iterables.
Create uses a generator, update and delete use async generators, and PATCH
uses (identifier, payload) pairs. Results keep the order of their inputs.
"""

import asyncio
from collections.abc import AsyncIterator, Iterable
from typing import assert_type
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import BaseSchema, Field, ReadField
from fastsprout.core.types import AnyIterable
from fastsprout.data import DataR, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=100)


class HeroPatch(BaseSchema):
    power: Field[int]


heroes = DataS(Hero, patch=HeroPatch)


async def async_items[T](items: Iterable[T]) -> AsyncIterator[T]:
    for item in items:
        yield item


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        async with DataR() as datar:
            payloads: AnyIterable[Hero] = (
                heroes.create_schema(name=name) for name in ("Batman", "Robin")
            )
            created = await heroes.bulk_create(payloads, datar=datar).to_list()
            assert_type(created, list[Hero])
            print("Created:", [(hero.name, hero.power) for hero in created])

            updated = await heroes.bulk_update(
                async_items(
                    hero.model_copy(update={"power": hero.power + 1})
                    for hero in created
                ),
                datar=datar,
            ).to_list()
            assert_type(updated, list[Hero])
            print("Updated:", [(hero.name, hero.power) for hero in updated])

            replaced = await heroes.bulk_update(
                (
                    (hero.id, heroes.update_schema(name=hero.name, power=150))
                    for hero in updated
                ),
                datar=datar,
            ).to_list()
            print(
                "Updated by key:",
                [(hero.name, hero.power) for hero in replaced],
            )

            patched = await heroes.bulk_patch(
                ((hero.id, HeroPatch(power=200)) for hero in replaced),
                datar=datar,
            ).to_list()
            print("Patched:", [(hero.name, hero.power) for hero in patched])

            deleted = await heroes.bulk_delete(
                async_items(hero.id for hero in patched), datar=datar
            )
            print("Deleted:", deleted)
            print("Remaining:", await heroes.count(datar=datar))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
