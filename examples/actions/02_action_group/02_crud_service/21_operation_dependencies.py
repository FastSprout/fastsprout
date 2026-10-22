"""Let the injector create a Service for DataS operation dependencies.
Both access and audit use the same HeroChecks instance within an operation.
The next operation gets a new instance. Deletion is rejected by the policy.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Service, action
from fastsprout.actions.service.datas import DataSOperation
from fastsprout.core import Depends, Field, ReadField
from fastsprout.data import DataR, sql


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


class HeroChecks(Service):
    def __init__(self, *, can_delete: bool = False) -> None:
        super().__init__()
        self.can_delete = can_delete
        print("Checks created")

    @action
    async def access(self, operation: DataSOperation) -> None:
        print("Checking:", operation)
        if operation == "delete" and not self.can_delete:
            raise PermissionError("Deleting is forbidden")

    @action
    async def audit(self, operation: DataSOperation) -> None:
        print("Allowed:", operation)


heroes = DataS(
    Hero,
    dependencies=[Depends(HeroChecks.access), HeroChecks.audit.dependency],
)


async def main() -> None:
    async with database():
        async with DataR() as datar:
            created = await heroes.create(Hero(name="Batman"), datar=datar)
            print("Created:", created.name)
            try:
                await heroes.delete(created.id, datar=datar)
            except PermissionError as error:
                print("Rejected:", error)
            print("Still exists:", await heroes.exists(created.id, datar=datar))


if __name__ == "__main__":
    asyncio.run(main())
