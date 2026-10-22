"""Share an explicitly configured Service instance across DataS operations.
Depends(checks.access) and checks.audit.dependency keep the supplied object.
This instance permits deletion and is reused for create, delete, and exists.
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


checks = HeroChecks(can_delete=True)
heroes = DataS(
    Hero,
    dependencies=[Depends(checks.access), checks.audit.dependency],
)


async def main() -> None:
    async with database():
        async with DataR() as datar:
            created = await heroes.create(Hero(name="Batman"), datar=datar)
            print("Created:", created.name)
            await heroes.delete(created.id, datar=datar)
            print("Deleted:", created.name)
            print("Still exists:", await heroes.exists(created.id, datar=datar))


if __name__ == "__main__":
    asyncio.run(main())
