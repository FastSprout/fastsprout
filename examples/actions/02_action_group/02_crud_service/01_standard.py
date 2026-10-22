"""DataS — standard."""

import asyncio
from typing import assert_type
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadField
from fastsprout.data import sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(
        default_factory=uuid4,
        primary_key=True,
    )
    name: Field[str]
    power: Field[int]


heroes = DataS(Hero)


async def main() -> None:
    async with database():
        created = await heroes.create(
            Hero(
                name="Batman",
                power=100,
            )
        )
        assert_type(created, Hero)

        found = await heroes.get(created.id)
        assert_type(found, Hero | None)

        assert found is not None

        updated = await heroes.update(
            found.model_copy(
                update={"power": 101},
            )
        )
        assert_type(updated, Hero)

        await heroes.delete(updated.id)

        print(found.name, updated.power, "deleted")


if __name__ == "__main__":
    asyncio.run(main())
