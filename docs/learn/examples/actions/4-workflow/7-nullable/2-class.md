# 2. Class

<!-- example-source: examples/actions/04_workflow/07_nullable/02_class.py -->

Use a BaseNullableAction class as a workflow step.
A missing document produces no elements, so the next action does not run.

## Source

```python
"""Use a BaseNullableAction class as a workflow step.
A missing document produces no elements, so the next action does not run.
"""

import asyncio

from fastsprout.actions import Workflow
from fastsprout.core import BaseSchema
from fastsprout.core.action import BaseNullableAction


class DocumentRequest(BaseSchema):
    name: str


class Document(BaseSchema):
    content: str


class FindDocument(BaseNullableAction[DocumentRequest, Document]):
    async def __call__(self, payload: DocumentRequest) -> Document | None:
        if payload.name == "guide":
            return Document(content="FastSprout")
        return None


class Render:
    async def __call__(self, document: Document) -> Document:
        return Document(content=document.content.upper())


lookup = Workflow(FindDocument()).then(Render())


async def main() -> None:
    for name in ("guide", "missing"):
        print("Looking up:", name)
        async for document in lookup(DocumentRequest(name=name)):
            print(document)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Looking up: guide
content='FASTSPROUT'
Looking up: missing
```
