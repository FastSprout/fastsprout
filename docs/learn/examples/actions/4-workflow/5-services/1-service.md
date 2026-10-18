# 1. Service

<!-- example-source: examples/actions/04_workflow/05_services/01_service.py -->

Build a workflow from typed methods of nested action services.
The document passes from preparation through rendering to signing.

## Source

```python
"""Build a workflow from typed methods of nested action services.
The document passes from preparation through rendering to signing."""

import asyncio

from fastsprout.actions import Workflow, action
from fastsprout.core import BaseSchema, Depends


class Document(BaseSchema):
    content: str


class RenderedDocument(BaseSchema):
    content: bytes


class SignedDocument(BaseSchema):
    content: bytes
    signature: str


@action
class DocumentRenderer:
    async def render(
        self,
        document: Document,
    ) -> RenderedDocument:
        return RenderedDocument(content=document.content.encode())


@action
class DocumentSigner:
    async def sign(
        self,
        document: RenderedDocument,
    ) -> SignedDocument:
        return SignedDocument(
            content=document.content,
            signature=f"signed:{len(document.content)}",
        )


@action
class DocumentService:
    renderer: DocumentRenderer = Depends()
    signer: DocumentSigner = Depends()

    async def prepare(
        self,
        document: Document,
    ) -> Document:
        return Document(
            content=document.content.strip(),
        )


documents = DocumentService()

workflow = (
    Workflow(documents.prepare)
    .then(documents.renderer.render)
    .then(documents.signer.sign)
)


async def main() -> None:
    async for signed in workflow(Document(content="FastSprout")):
        print(signed)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
content=b'FastSprout' signature='signed:10'
```
