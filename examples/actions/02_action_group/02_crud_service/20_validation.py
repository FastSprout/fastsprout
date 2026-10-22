"""Compose @action dependencies for validation, normalization, and delete protection.
Configure DataS with .dependency or Depends(action).
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, WriteOperation, action
from fastsprout.core import Depends, Field, ReadField
from fastsprout.data import DataR, sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=100)


async def check_power(entity: Hero) -> None:
    if entity.power < 0:
        raise ValueError("Power must be non-negative")


@action(dependencies=[Depends(check_power)])
async def normalize_hero(entity: Hero) -> None:
    entity.name = entity.name.strip()


@action
async def protect_delete(operation: WriteOperation) -> None:
    if operation == "delete":
        raise PermissionError("Deleting heroes is forbidden")


heroes = DataS(Hero, dependencies=[Depends(protect_delete)])
creator = DataS(Hero, dependencies=[normalize_hero.dependency])


async def main() -> None:
    async with database():
        async with DataR() as datar:
            created = await creator.create(
                creator.create_schema(name="  Batman  "), datar=datar
            )
            print("Created:", created.name, created.power)
            try:
                await creator.create(
                    creator.create_schema(name="Robin", power=-1), datar=datar
                )
            except ValueError as error:
                print("Rejected:", error)
            try:
                await heroes.delete(created.id, datar=datar)
            except PermissionError as error:
                print("Rejected:", error)


if __name__ == "__main__":
    asyncio.run(main())
