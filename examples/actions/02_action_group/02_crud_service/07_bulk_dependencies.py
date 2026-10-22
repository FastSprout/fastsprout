"""Combine batch access checks, model validation, and DataR dependencies.
Dependencies run once per chunk before its write. Service and router
dependencies share one DataR; deleting the batch is denied separately.
"""

import asyncio
from collections.abc import Sequence
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.actions.service.datas import DataSOperation
from fastsprout.core import Depends, Field, ReadField, dataclass
from fastsprout.data import DataR, sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=100)


@dataclass(frozen=True)
class Actor:
    can_delete: bool


async def current_actor() -> Actor:
    return Actor(can_delete=False)


def check_access(
    operation: DataSOperation,
    datar: DataR,
    actor: Actor = Depends(current_actor),
) -> None:
    if operation == "bulk_delete" and not actor.can_delete:
        raise PermissionError("Deleting batches is forbidden")
    print("Action:", operation)


def validate_heroes(entities: Sequence[Hero] = ()) -> None:
    for entity in entities:
        if entity.power < 0:
            raise ValueError("Power must be non-negative")
        entity.name = entity.name.strip()


def observe_backend(operation: str, datar: DataR) -> None:
    if operation == "bulk_create":
        print("Backend:", operation)


context = DataR(
    dependencies=[Depends(validate_heroes), Depends(observe_backend)]
)
heroes = DataS(Hero, chunk_size=2, dependencies=[Depends(check_access)])
catalog = DataS(Hero)


async def main() -> None:
    async with database():
        async with context as datar:
            try:
                await heroes.bulk_create(
                    (
                        heroes.create_schema(name=name, power=power)
                        for name, power in (("Batman", 100), ("Robin", -1))
                    ),
                    datar=datar,
                ).to_list()
            except ValueError as error:
                print("Rejected:", error)
            print("After rejected batch:", await catalog.count(datar=datar))

            identifiers: list[UUID] = []
            async for hero in heroes.bulk_create(
                (
                    heroes.create_schema(name=name)
                    for name in ("  Batman  ", "Robin", "Batgirl")
                ),
                datar=datar,
            ):
                identifiers.append(hero.id)
                print("Created:", hero.name)

            try:
                await heroes.bulk_delete(iter(identifiers), datar=datar)
            except PermissionError as error:
                print("Rejected:", error)
            print("Remaining:", await catalog.count(datar=datar))


if __name__ == "__main__":
    asyncio.run(main())
