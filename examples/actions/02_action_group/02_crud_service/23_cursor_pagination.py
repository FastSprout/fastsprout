"""Continue from an entity cursor and consume a stream in chunks.
copy() keeps the base query unchanged; after() continues past the previous row.
Each chunk contains at most two heroes inside the same DataR transaction.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadField
from fastsprout.data import DataR, sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int]


heroes = DataS(Hero)


async def main() -> None:
    async with database():
        async with DataR() as datar:
            async for hero in heroes.bulk_create(
                (
                    Hero(name=name, power=power)
                    for name, power in (
                        ("Batman", 80),
                        ("Robin", 40),
                        ("Batgirl", 60),
                    )
                ),
                datar=datar,
            ):
                print("Created:", hero.name)

            query = sql.SQLQuery(Hero).order_by(Hero.power, reverse=True)
            first = await heroes.list(query.copy().limit(1), datar=datar)
            second = await heroes.list(
                query.copy().after(first.items[0]).limit(1), datar=datar
            )
            print("First page:", first.items[0].name)
            print("Next page:", second.items[0].name)

            async for chunk in heroes.stream(query, datar=datar).chunked(2):
                print("Chunk:", tuple(hero.name for hero in chunk))


if __name__ == "__main__":
    asyncio.run(main())
