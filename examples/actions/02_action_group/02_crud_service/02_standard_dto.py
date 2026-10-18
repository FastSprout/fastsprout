"""DataS — custom DTO."""

import asyncio
from typing import assert_type
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadDTO, ReadField, inject_depends
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


class HeroRead(ReadDTO, Hero):
    def label(self) -> str:
        return f"{self.name}: {self.power}"


heroes = DataS(
    Hero,
    read=HeroRead,
)


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

    found = await heroes.get(created.id)
    assert_type(found, HeroRead | None)

    assert found is not None
    print(found.label())

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
