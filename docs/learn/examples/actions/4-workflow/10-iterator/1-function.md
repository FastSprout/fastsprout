# 1. Function

<!-- example-source: examples/actions/04_workflow/10_iterator/01_function.py -->

Nest async iterator workflows and consume their results lazily.
The stream also works as IteratorActionable and feeds each document to render.

## Source

```python
"""Nest async iterator workflows and consume their results lazily.
The stream also works as IteratorActionable and feeds each document to render.
"""

import asyncio
from collections.abc import AsyncIterator

from fastsprout.actions import Workflow
from fastsprout.core import BaseSchema
from fastsprout.core.action import IteratorActionable


class DocumentRequest(BaseSchema):
    contents: tuple[str, ...]


class Document(BaseSchema):
    content: str


class RenderedDocument(BaseSchema):
    content: bytes


async def load(request: DocumentRequest) -> AsyncIterator[Document]:
    for text in request.contents:
        await asyncio.sleep(0)
        print("Reading:", text)
        yield Document(content=text)


async def render(document: Document) -> RenderedDocument:
    return RenderedDocument(content=document.content.encode())


load_documents = Workflow(load)
nested = Workflow(load_documents)
stream: IteratorActionable[DocumentRequest, Document] = nested
workflow = Workflow(stream).then(render)


async def main() -> None:
    request = DocumentRequest(contents=("Guide", "Reference"))
    documents = workflow(request)
    print("Stream ready; documents have not been read yet")
    async for document in documents:
        print(document)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Stream ready; documents have not been read yet
Reading: Guide
content=b'Guide'
Reading: Reference
content=b'Reference'
```
