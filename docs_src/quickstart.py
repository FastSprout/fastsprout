"""Prepare one typed task draft and print its result."""

import asyncio

from fastsprout.actions import action
from fastsprout.core import BaseSchema


class NewTask(BaseSchema):
    title: str


class TaskDraft(BaseSchema):
    title: str


@action
async def prepare_task(payload: NewTask) -> TaskDraft:
    return TaskDraft(title=payload.title.strip())


async def main() -> None:
    draft = await prepare_task(NewTask(title="  Write documentation  "))
    print(draft.title)


if __name__ == "__main__":
    asyncio.run(main())
