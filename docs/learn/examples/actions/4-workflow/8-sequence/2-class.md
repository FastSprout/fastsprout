# 2. Class

<!-- example-source: examples/actions/04_workflow/08_sequence/02_class.py -->

Compose a BaseSequenceAction class with a rendering action.
The renderer receives one document at a time from the sequence.

## Source

```python
"""Compose a BaseSequenceAction class with a rendering action.
The renderer receives one document at a time from the sequence.
"""

import asyncio
from collections.abc import Sequence

from fastsprout.actions import Workflow
from fastsprout.core import BaseSchema
from fastsprout.core.action import BaseSequenceAction


class DocumentRequest(BaseSchema):
    contents: tuple[str, ...]


class Document(BaseSchema):
    content: str


class RenderedDocument(BaseSchema):
    content: bytes


class LoadDocuments(BaseSequenceAction[DocumentRequest, Document]):
    async def __call__(self, payload: DocumentRequest) -> Sequence[Document]:
        return tuple(Document(content=text) for text in payload.contents)


class Render:
    async def __call__(self, document: Document) -> RenderedDocument:
        return RenderedDocument(content=document.content.encode())


workflow = Workflow(LoadDocuments()).then(Render())


async def main() -> None:
    request = DocumentRequest(contents=("Guide", "Reference"))
    async for document in workflow(request):
        print(document)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
content=b'Guide'
content=b'Reference'
```
