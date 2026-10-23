"""Compare committed service calls with two writes rolled back together."""

import asyncio

from docs_src.data.common import Task, database
from docs_src.data.quickstart import tasks
from fastsprout.data import DataR


async def main() -> None:
    async with database():
        try:
            await tasks.create(Task(id=1, title="Write documentation"))
            await tasks.create(Task(id=2, title="Review documentation"))
            raise ValueError("Stop this operation")
        except ValueError:
            separate_count = await tasks.count()
            assert separate_count == 2
            print("Separate calls after error:", separate_count)

        await tasks.delete(1)
        await tasks.delete(2)

        try:
            async with DataR() as datar:
                await tasks.create(
                    Task(id=1, title="Write documentation"), datar=datar
                )
                await tasks.create(
                    Task(id=2, title="Review documentation"), datar=datar
                )
                raise ValueError("Stop this operation")
        except ValueError:
            shared_count = await tasks.count()
            assert shared_count == 0
            print("Shared context after error:", shared_count)


if __name__ == "__main__":
    asyncio.run(main())
