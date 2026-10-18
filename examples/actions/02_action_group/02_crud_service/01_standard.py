"""DataS — standard."""

import asyncio
from typing import assert_type
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadField, inject_depends
from fastsprout.data import DataR, provide_datar, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY, SQLSignpost

engine = create_async_engine(
    "sqlite+aiosqlite://",
    poolclass=StaticPool,
)

backend = SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(
        default_factory=uuid4,
        primary_key=True,
    )
    name: Field[str]
    power: Field[int]


heroes = DataS(Hero)


async def main() -> None:
    inject_depends.dependency_providers[DataR] = provide_datar
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    created = await heroes.create(
        Hero(
            name="Batman",
            power=100,
        )
    )
    assert_type(created, Hero)

    found = await heroes.get(created.id)
    assert_type(found, Hero | None)

    assert found is not None

    updated = await heroes.update(
        found.model_copy(
            update={"power": 101},
        )
    )
    assert_type(updated, Hero)

    await heroes.delete(updated.id)

    print(found.name, updated.power, "deleted")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
