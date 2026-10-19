"""Read one match, all matches, or a lazy stream through the same Query.
An explicit read DTO controls the fields returned by every read operation.
DataR binds the entity to its ability: `query_for()` and `query_for(Hero)`
create equivalent queries.
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


heroes = DataS(Hero, read=HeroRead)


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Hero.__table__.create)
        async with DataR() as datar:
            await heroes.bulk_create(
                (
                    Hero(name=name, power=power)
                    for name, power in (("Batman", 80), ("Robin", 50))
                ),
                datar=datar,
            ).to_list()
            query = datar.ability(Hero).query_for().order_by(Hero.power)
            first = await heroes.find_first(query, datar=datar)
            print("First:", first.name if first else None)
            only = await heroes.find_exactly_one(
                query.copy().where(Hero.name.eq("Batman")), datar=datar
            )
            print("Exactly one:", only.name)
            matches = await heroes.find_all(query, datar=datar)
            print("All:", [hero.name for hero in matches])
            async for hero in heroes.stream(query, datar=datar):
                print("Stream:", hero.name)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
