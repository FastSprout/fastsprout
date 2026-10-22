"""Use the entity, supply a custom schema, or disable an operation.
Undefined keeps defaults; a schema class overrides them; None disables CRUD.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import (
    BaseSchema,
    Field,
    ReadField,
    Undefined,
)
from fastsprout.data import sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=100)


class HeroCreate(BaseSchema):
    name: Field[str]
    power: Field[int] = Field(default=20)


default = DataS(Hero, create=Undefined)
custom = DataS(Hero, create=HeroCreate)
catalog = DataS(Hero, create=None, update=None, patch=None)


async def main() -> None:
    async with database():
        batman = await default.create(default.create_schema(name="Batman"))
        print("Entity schema:", batman.name, batman.power)

        robin = await custom.create(HeroCreate(name="Robin"))
        print("Custom schema:", robin.name, robin.power)

        print("Create enabled:", "create" in catalog.operations)
        print("Catalog count:", await catalog.count())


if __name__ == "__main__":
    asyncio.run(main())
