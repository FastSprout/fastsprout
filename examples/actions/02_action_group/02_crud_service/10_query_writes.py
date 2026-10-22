"""Update and delete a selection using Query conditions, ordering, and limits.
Both operations return the number of affected records.
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
            await heroes.bulk_create(
                (
                    Hero(name=name, power=power)
                    for name, power in (("Batman", 80), ("Robin", 50))
                ),
                datar=datar,
            ).to_list()
            query = datar.ability(Hero).query_for(Hero)
            selection = query.copy().where(Hero.name.eq("Robin"))
            updated = await heroes.update_by_query(
                selection, Hero.power.set(60), datar=datar
            )
            print("Updated:", updated)
            async for hero in heroes.stream(
                query.order_by(Hero.power), datar=datar
            ):
                print(hero.name, hero.power)
            deleted = await heroes.delete_by_query(
                query.copy().limit(1), datar=datar
            )
            print("Deleted:", deleted)
            print("Remaining:", await heroes.count(datar=datar))


if __name__ == "__main__":
    asyncio.run(main())
