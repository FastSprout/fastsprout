"""Select pending tasks, read a page, and stream the same selection."""

import asyncio

from docs_src.data.common import Task, database
from docs_src.data.quickstart import tasks
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLQuery


async def main() -> None:
    async with database():
        await tasks.create(Task(id=1, title="Write documentation"))
        await tasks.create(Task(id=2, title="Review documentation"))
        await tasks.create(Task(id=3, title="Ship release", completed=True))

        pending = (
            SQLQuery(Task)
            .where(Task.completed.eq(False))
            .order_by(Task.id)
            .limit(1)
        )
        page = await tasks.list(pending)
        print("Matching tasks:", page.total)
        print("Page:", [task.title for task in page.items])

        async with DataR() as datar:
            async for task in datar.stream(pending):
                print("Streamed:", task.title)


if __name__ == "__main__":
    asyncio.run(main())
