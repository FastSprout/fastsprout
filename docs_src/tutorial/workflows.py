"""Connect the checked preparation action to a typed formatting step."""

import asyncio

from docs_src.quickstart import NewTask, TaskDraft
from docs_src.tutorial.shared_checks import prepare_task
from fastsprout.actions import Workflow, action


@action
async def uppercase_title(draft: TaskDraft) -> TaskDraft:
    return TaskDraft(title=draft.title.upper())


workflow = Workflow(prepare_task).then(uppercase_title)


async def main() -> None:
    async for draft in workflow(NewTask(title="  Write documentation  ")):
        print(draft.title)


if __name__ == "__main__":
    asyncio.run(main())
