"""Check whether a primary key exists without loading a read DTO.
The result changes after create and delete.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadField
from fastsprout.data import sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


heroes = DataS(Hero)


async def main() -> None:
    async with database():
        missing = await heroes.exists(uuid4())
        print("Unknown key:", missing)

        created = await heroes.create(heroes.create_schema(name="Batman"))
        print("After create:", await heroes.exists(created.id))

        await heroes.delete(created.id)
        print("After delete:", await heroes.exists(created.id))


if __name__ == "__main__":
    asyncio.run(main())
