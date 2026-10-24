"""Group the checked actions without reimplementing their bodies."""

import asyncio

from docs_src.quickstart import NewTask
from docs_src.tutorial.shared_checks import prepare_task, preview_task
from fastsprout.actions import Service


class TaskService(Service):
    prepare = prepare_task
    preview = preview_task


tasks = TaskService()


async def main() -> None:
    payload = NewTask(title="Write documentation")
    draft = await tasks.prepare(payload)
    print("Prepared:", draft.title)
    print("Preview:", await tasks.preview(payload))
    try:
        await tasks.preview(NewTask(title=""))
    except ValueError as error:
        print("Rejected:", error)


if __name__ == "__main__":
    asyncio.run(main())
