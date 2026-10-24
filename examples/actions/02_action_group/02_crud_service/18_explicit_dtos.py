"""Configure explicit read and write DTOs without repeating entity fields.
DataS uses the entity for operations without a configured schema.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import (
    Field,
    InternalField,
    ReadDTO,
    ReadField,
    WriteDTO,
    WriteField,
)
from fastsprout.data import sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=100)
    password: WriteField[str]
    audit_tag: InternalField[str] = InternalField(default="system")


class HeroCreate(WriteDTO, Hero): ...


class HeroRead(ReadDTO, Hero): ...


heroes = DataS(Hero, create=HeroCreate, read=HeroRead)


async def main() -> None:
    async with database():
        payload = heroes.create_schema(name="Batman", password="secret")

        print("Create DTO fields:", sorted(vars(payload)))
        created = await heroes.create(payload)
        print("Created:", created.name, created.power)
        print("Read DTO fields:", sorted(vars(created)))


if __name__ == "__main__":
    asyncio.run(main())
