"""Create and update related entities through the backend's ORM cascades.
The query explicitly loads relationships so they remain available after reading.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadField
from fastsprout.data import DataR, Relationship, sql


class Team(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    team: Field[Team] = Relationship()


heroes = DataS(Hero)


async def main() -> None:
    async with database():
        async with DataR() as datar:
            created = await heroes.create(
                Hero(name="Batman", team=Team(name="Justice League")),
                datar=datar,
            )
            query = sql.SQLQuery(
                Hero,
                statement=select(Hero)
                .where(Hero.__table__.c.id == created.id)
                .options(selectinload("*")),
            )
            found = await heroes.find_exactly_one(query, datar=datar)
            found.team.name = "Justice League International"
            updated = await heroes.update(found, datar=datar)
            print(updated.name, "belongs to", updated.team.name)


if __name__ == "__main__":
    asyncio.run(main())
