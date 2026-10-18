"""Use the entity, supply a custom schema, or disable an operation.
Undefined keeps defaults; a schema class overrides them; None disables CRUD.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import (
    BaseSchema,
    Field,
    ReadField,
    Undefined,
    inject_depends,
)
from fastsprout.data import DataR, provide_datar, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=100)


class HeroCreate(BaseSchema):
    name: Field[str]
    power: Field[int] = Field(default=20)


default = DataS(Hero, create=Undefined)
custom = DataS(Hero, create=HeroCreate)
catalog = DataS(Hero, create=None, update=None, patch=None)


async def main() -> None:
    inject_depends.dependency_providers[DataR] = provide_datar
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        batman = await default.create(default.create_schema(name="Batman"))
        print("Entity schema:", batman.name, batman.power)

        robin = await custom.create(HeroCreate(name="Robin"))
        print("Custom schema:", robin.name, robin.power)

        print("Create enabled:", "create" in catalog.operations)
        print("Catalog count:", await catalog.count())
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
