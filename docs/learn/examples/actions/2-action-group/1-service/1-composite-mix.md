# 1. Composite Mix

<!-- example-source: examples/actions/02_action_group/01_service/01_composite_mix.py -->

Action service — composite mix of function and service.

## Source

```python
"""Action service — composite mix of function and service."""

import asyncio
from typing import assert_type

from pydantic import SecretStr

from fastsprout.actions import Service, action
from fastsprout.core import BaseSchema, Depends, Field


class Document(BaseSchema):
    content: Field[str]


class SignedDocument(BaseSchema):
    content: Field[bytes]
    signature: Field[SecretStr]


@action
async def render_document(document: Document) -> bytes:
    return document.content.encode()


@action
class DocumentSigner:
    async def sign(self, content: bytes) -> SignedDocument:
        return SignedDocument(
            content=content,
            signature=SecretStr(f"signed:{len(content)}"),
        )


class DocumentService(Service):
    render = render_document
    signer: DocumentSigner = Depends()


async def main() -> None:
    documents = DocumentService()
    document = Document(content="FastSprout")

    content = await documents.render(document)
    assert_type(content, bytes)

    signed = await documents.signer.sign(content)
    assert_type(signed, SignedDocument)
    print(signed.content, signed.signature.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
b'FastSprout' signed:10
```
