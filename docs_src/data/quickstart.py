"""Create, query, and complete a task through DataS and one DataR context."""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Depends, Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
store = SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Task(SQLEntity[int]):
    __signpost__ = store

    id: ReadField[int] = SQLField(primary_key=True)
    title: Field[str]
    completed: Field[bool] = Field(default=False)


class Tasks(DataS[Task]):
    async def complete(self, identifier: int, datar: DataR = Depends()) -> Task:
        task = await self.get(identifier, datar=datar)
        if task is None:
            raise LookupError(f"Task {identifier} does not exist")
        return await self.update(
            task.model_copy(update={"completed": True}), datar=datar
        )


tasks = Tasks()


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        async with DataR() as datar:
            created = await tasks.create(
                Task(id=1, title="Write documentation"), datar=datar
            )
            print("Created:", created.title)

            pending = SQLQuery(Task).where(Task.completed.eq(False))
            page = await tasks.list(pending, datar=datar)
            print("Pending:", page.total)

            completed = await tasks.complete(created.id, datar=datar)
            print("Completed:", completed.completed)

            remaining = await datar.stream(pending).count()
            print("Remaining:", remaining)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
