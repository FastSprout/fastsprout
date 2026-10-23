"""Create and retrieve a task using DataS's existing CRUD operations."""

import asyncio

from docs_src.data.common import Task, database
from fastsprout.actions import DataS

tasks = DataS(Task)


async def main() -> None:
    async with database():
        created = await tasks.create(Task(id=1, title="Write documentation"))
        print("Created:", created.id, created.title)
        found = await tasks.get(created.id)
        if found is not None:
            print("Found:", found.id, found.title)
        print("Missing:", await tasks.get(999))


if __name__ == "__main__":
    asyncio.run(main())
