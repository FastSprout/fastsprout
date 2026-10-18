"""Replace each input chunk before the next dependency and backend write.
Returning Chunk replaces the batch; returning None keeps the current batch.
Only two inputs are read at a time, including for an async input generator.
"""

import asyncio
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Chunk, Depends, Field, ReadField
from fastsprout.data import DataR, sql

engine = create_async_engine("sqlite+aiosqlite://")
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


def named_heroes(entities: Chunk[Hero]) -> Chunk[Hero]:
    return Chunk(hero async for hero in entities if hero.name.strip())


def normalize(entities: Chunk[Hero]) -> Chunk[Hero]:
    async def normalized() -> AsyncIterator[Hero]:
        names: list[str] = []
        async for hero in entities:
            hero.name = hero.name.strip()
            names.append(hero.name)
            yield hero
        print("Prepared chunk:", names)

    return Chunk(normalized())


heroes = DataS(
    Hero,
    chunk_size=2,
    dependencies=[Depends(named_heroes), Depends(normalize)],
)


async def incoming() -> AsyncIterator[Hero]:
    for name in (" Batman ", " ", "Robin"):
        yield heroes.create_schema(name=name)


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Hero.__table__.create)
        async with DataR() as datar:
            async for hero in heroes.bulk_create(incoming(), datar=datar):
                print("Saved:", hero.name)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
