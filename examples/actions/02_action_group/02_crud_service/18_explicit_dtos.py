"""Configure explicit read and write DTOs without repeating entity fields.
DataS uses the entity for operations without a configured schema.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import (
    Field,
    InternalField,
    ReadDTO,
    ReadField,
    WriteDTO,
    WriteField,
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
    password: WriteField[str]
    audit_tag: InternalField[str] = InternalField(default="system")


class HeroCreate(WriteDTO, Hero): ...


class HeroRead(ReadDTO, Hero): ...


heroes = DataS(Hero, create=HeroCreate, read=HeroRead)


async def main() -> None:
    inject_depends.dependency_providers[DataR] = provide_datar
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        payload = heroes.create_schema(name="Batman", password="secret")

        print("Create DTO fields:", sorted(vars(payload)))
        created = await heroes.create(payload)
        print("Created:", created.name, created.power)
        print("Read DTO fields:", sorted(vars(created)))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
