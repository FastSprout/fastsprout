"""Map read results into a custom response schema with an async function."""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import BaseSchema, Field, InternalField, ReadField
from fastsprout.data import DataR, sql


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
    async with database():
        async with DataR() as datar:
            await heroes.create(Hero(name="Batman"), datar=datar)
            async for summary in heroes.map(
                sql.SQLQuery(Hero), summarize, datar=datar
            ):
                print(summary.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
