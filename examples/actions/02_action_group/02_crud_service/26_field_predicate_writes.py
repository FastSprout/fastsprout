"""Use field conditions or SQLQuery to stream and write matching records.
All conditions are combined with AND: a record must match every condition.
Pass either a SQLQuery with its conditions or field predicates directly.
DataS preserves Query entity and visibility checks and returns affected counts.
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
            for name, power in (("Batman", 80), ("Robin", 50), ("Batgirl", 50)):
                await heroes.create(Hero(name=name, power=power), datar=datar)
            selection = Hero.name.eq("Robin")
            updated = await heroes.update_by_query(
                Hero.power.eq(50), selection, Hero.power.set(60), datar=datar
            )
            print("Updated:", updated)
            async for hero in heroes.stream(
                Hero.power.gte(50), selection, datar=datar
            ):
                print("Matched:", hero.name, hero.power)
            async for hero in heroes.stream(
                sql.SQLQuery(Hero).order_by(Hero.power), datar=datar
            ):
                print(hero.name, hero.power)
            deleted = await heroes.delete_by_query(
                Hero.power.lt(70), selection, datar=datar
            )
            print("Deleted:", deleted)
            print("Remaining:", await heroes.count(datar=datar))
            query = sql.SQLQuery(Hero).where(
                Hero.power.eq(50), Hero.name.eq("Batgirl")
            )
            updated = await heroes.update_by_query(
                query, Hero.power.set(70), datar=datar
            )
            print("SQLQuery updated:", updated)
            deleted = await heroes.delete_by_query(
                sql.SQLQuery(Hero).where(
                    Hero.power.eq(70), Hero.name.eq("Batgirl")
                ),
                datar=datar,
            )
            print("SQLQuery deleted:", deleted)
            print("Remaining:", await heroes.count(datar=datar))


if __name__ == "__main__":
    asyncio.run(main())
