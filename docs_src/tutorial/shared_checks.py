"""Reuse a title check in two actions and reject an empty title."""

import asyncio

from docs_src.quickstart import NewTask, TaskDraft
from docs_src.quickstart import prepare_task as normalize_task
from fastsprout.actions import action
from fastsprout.core import Depends


async def require_title(payload: NewTask) -> None:
    if not payload.title.strip():
        raise ValueError("Task title cannot be empty")


@action(dependencies=[Depends(require_title)])
async def prepare_task(payload: NewTask) -> TaskDraft:
    return await normalize_task(payload)


@action(dependencies=[Depends(require_title)])
async def preview_task(payload: NewTask) -> str:
    draft = await normalize_task(payload)
    return f"Task: {draft.title}"


async def main() -> None:
    payload = NewTask(title="  Write documentation  ")
    draft = await prepare_task(payload)
    print("Prepared:", draft.title)
    print("Preview:", await preview_task(payload))
    try:
        await prepare_task(NewTask(title="   "))
    except ValueError as error:
        print("Rejected:", error)


if __name__ == "__main__":
    asyncio.run(main())
