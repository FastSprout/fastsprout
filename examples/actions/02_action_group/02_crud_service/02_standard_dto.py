"""DataS — custom DTO."""

import asyncio
from typing import assert_type
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadDTO, ReadField
from fastsprout.data import sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(
        default_factory=uuid4,
        primary_key=True,
    )
    name: Field[str]
    power: Field[int]


class HeroRead(ReadDTO, Hero):
    def label(self) -> str:
        return f"{self.name}: {self.power}"


heroes = DataS(
    Hero,
    read=HeroRead,
)


async def main() -> None:
    async with database():
        created = await heroes.create(
            Hero(
                name="Batman",
                power=100,
            )
        )

        found = await heroes.get(created.id)
        assert_type(found, HeroRead | None)

        assert found is not None
        print(found.label())


if __name__ == "__main__":
    asyncio.run(main())
