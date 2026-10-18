"""Map read results into a custom response schema with an async function."""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import BaseSchema, Field, InternalField, ReadField
from fastsprout.data import DataR, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://")
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    secret: InternalField[str] = InternalField(default="hidden")


class HeroSummary(BaseSchema):
    label: str


heroes = DataS(Hero)


async def summarize(hero: Hero) -> HeroSummary:
    return HeroSummary(label=hero.name.upper())


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
        async with DataR() as datar:
            await heroes.create(Hero(name="Batman"), datar=datar)
            async for summary in heroes.map(
                sql.SQLQuery(Hero), summarize, datar=datar
            ):
                print(summary.model_dump_json())
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
