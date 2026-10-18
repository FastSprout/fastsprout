"""Insert new entities or update existing ones using their identifiers.
Bulk upserts consume iterable inputs in chunks and return the configured read DTO.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadDTO, ReadField
from fastsprout.data import DataR, sql

engine = create_async_engine("sqlite+aiosqlite://")
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int]


class HeroRead(ReadDTO, Hero): ...


heroes = DataS(Hero, read=HeroRead, chunk_size=2)


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Hero.__table__.create)
        async with DataR() as datar:
            created = await heroes.upsert(
                Hero(name="Batman", power=80), datar=datar
            )
            print("Inserted:", created.name, created.power)
            updated = await heroes.upsert(
                Hero(id=created.id, name="Batman", power=90), datar=datar
            )
            print("Updated:", updated.name, updated.power)
            inputs = (
                hero
                for hero in (
                    Hero(name="Robin", power=50),
                    Hero(id=created.id, name="Batman", power=100),
                    Hero(name="Batgirl", power=70),
                )
            )
            async for hero in heroes.bulk_upsert(inputs, datar=datar):
                print(type(hero).__name__, hero.name, hero.power)
            print("Total:", await heroes.count(datar=datar))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
