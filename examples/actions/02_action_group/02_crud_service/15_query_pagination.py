"""Use query conditions and pagination.
Page.total and count describe the selection before pagination.
"""

import asyncio
from typing import Annotated
from uuid import UUID, uuid4

from common import backend, database
from pydantic import Field as PydanticField
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Page
from fastsprout.core import Field, ReadField
from fastsprout.data import DataR, sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int]


class HeroPage(Page[Hero]):
    limit: Annotated[int | None, PydanticField(ge=0, le=1000)] = 10


heroes = DataS(Hero, page=HeroPage)


async def main() -> None:
    async with database():
        async with DataR() as datar:
            for name, power in (
                ("Batman", 80),
                ("Batgirl", 100),
                ("Robin", 50),
            ):
                await heroes.create(
                    heroes.create_schema(name=name, power=power), datar=datar
                )

            query = (
                datar.ability(Hero)
                .query_for(Hero)
                .where(Hero.power.gte(80))
                .order_by(Hero.power, reverse=True)
                .offset(1)
                .limit(1)
            )
            page = await heroes.list(query, datar=datar)
            print("Page:", [hero.name for hero in page.items])
            print("Pagination:", page.total, page.offset, page.limit)

            count = await heroes.count(query, datar=datar)
            print("Matching heroes:", count)


if __name__ == "__main__":
    asyncio.run(main())
