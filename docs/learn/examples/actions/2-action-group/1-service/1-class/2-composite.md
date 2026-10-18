# 2. Composite

<!-- example-source: examples/actions/02_action_group/01_service/01_class/02_composite.py -->

Action service — composite.

## Source

```python
"""Action service — composite."""

import asyncio
from typing import assert_type

from fastsprout.actions import Service
from fastsprout.core import BaseSchema, Depends, Field


class Document(BaseSchema):
    content: Field[str]


class SignedDocument(BaseSchema):
    content: Field[bytes]
    signature: Field[str]


class DocumentRenderer(Service):
    async def render(self, document: Document) -> bytes:
        return document.content.encode()


class DocumentSigner(Service):
    renderer: DocumentRenderer = Depends()

    async def sign(self, document: Document) -> SignedDocument:
        content = await self.renderer.render(document)

        return SignedDocument(
            content=content,
            signature=f"signed:{len(content)}",
        )


class DocumentService(Service):
    renderer: DocumentRenderer = Depends()
    signer: DocumentSigner = Depends()


async def main() -> None:
    documents = DocumentService()
    document = Document(content="FastSprout")

    content = await documents.renderer.render(document)
    assert_type(content, bytes)

    signed = await documents.signer.sign(document)
    assert_type(signed, SignedDocument)
    print(signed)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
content=b'FastSprout' signature='signed:10'
```
