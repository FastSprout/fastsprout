"""Prepare a task through an action with a shared input check."""

import asyncio

from fastsprout.actions import action
from fastsprout.core import BaseSchema, Depends, Field


class NewTask(BaseSchema):
    title: Field[str]


class TaskDraft(BaseSchema):
    title: Field[str]


async def require_title(payload: NewTask) -> None:
    if not payload.title.strip():
        raise ValueError("Task title cannot be empty")


@action(dependencies=[Depends(require_title)])
async def prepare_task(payload: NewTask) -> TaskDraft:
    return TaskDraft(title=payload.title.strip())


async def main() -> None:
    draft = await prepare_task(NewTask(title="  Write documentation  "))
    print(draft.title)


if __name__ == "__main__":
    asyncio.run(main())
