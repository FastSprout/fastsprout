# 1. Function

<!-- example-source: examples/actions/04_workflow/07_nullable/01_function.py -->

A nullable action emits one document or no elements.
When find returns None, the render step does not run.

## Source

```python
"""A nullable action emits one document or no elements.
When find returns None, the render step does not run.
"""

import asyncio

from fastsprout.actions import Workflow
from fastsprout.core import BaseSchema
from fastsprout.core.action import NullableActionable


class DocumentRequest(BaseSchema):
    name: str


class Document(BaseSchema):
    content: str


async def find(request: DocumentRequest) -> Document | None:
    if request.name == "guide":
        return Document(content="FastSprout")
    return None


async def render(document: Document) -> Document:
    return Document(content=document.content.upper())


nullable: NullableActionable[DocumentRequest, Document] = find
lookup = Workflow(nullable).then(render)


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
