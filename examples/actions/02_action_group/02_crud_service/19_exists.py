"""Check whether a primary key exists without loading a read DTO.
The result changes after create and delete.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadField, inject_depends
from fastsprout.data import DataR, provide_datar, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


heroes = DataS(Hero)


async def main() -> None:
    inject_depends.dependency_providers[DataR] = provide_datar
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        missing = await heroes.exists(uuid4())
        print("Unknown key:", missing)

        created = await heroes.create(heroes.create_schema(name="Batman"))
        print("After create:", await heroes.exists(created.id))

        await heroes.delete(created.id)
        print("After delete:", await heroes.exists(created.id))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
