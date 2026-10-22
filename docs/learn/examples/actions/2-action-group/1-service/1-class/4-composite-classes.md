# 4. Composite Classes

<!-- example-source: examples/actions/02_action_group/01_service/01_class/04_composite_classes.py -->

Action service — composite classes.
Combine a function action, a class action, and a bound service method.
The service can also define its own methods using these actions.

## Source

```python
"""Action service — composite classes.
Combine a function action, a class action, and a bound service method.
The service can also define its own methods using these actions."""

import asyncio
from typing import assert_type

from fastsprout.actions import Action, Service, action
from fastsprout.core import BaseSchema, Field


class Document(BaseSchema):
    content: Field[str]


class RenderedDocument(BaseSchema):
    content: Field[bytes]


class SignedDocument(BaseSchema):
    content: Field[bytes]
    signature: Field[str]


@action
async def render_document(document: Document) -> RenderedDocument:
    return RenderedDocument(content=document.content.encode())


class SignDocument(Action[RenderedDocument, SignedDocument]):
    async def __call__(self, document: RenderedDocument) -> SignedDocument:
        return SignedDocument(
            content=document.content,
            signature=f"signed:{len(document.content)}",
        )


class DocumentVerifier(Service):
    async def verify(self, document: SignedDocument) -> bool:
        return document.signature == f"signed:{len(document.content)}"


verifier = DocumentVerifier()


class DocumentService(Service):
    render = render_document
    sign = SignDocument()
    verify = verifier.verify

    async def prepare(self, document: Document) -> SignedDocument:
        content = await self.render(document)
        return await self.sign(content)


async def main() -> None:
    documents = DocumentService()
    document = Document(content="FastSprout")

    content = await documents.render(document)
    assert_type(content, RenderedDocument)

    signed = await documents.sign(content)
    assert_type(signed, SignedDocument)

    verified = await documents.verify(signed)
    assert_type(verified, bool)

    prepared = await documents.prepare(document)
    assert_type(prepared, SignedDocument)
    print(prepared)
    print("Verified:", verified)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
content=b'FastSprout' signature='signed:10'
Verified: True
```
