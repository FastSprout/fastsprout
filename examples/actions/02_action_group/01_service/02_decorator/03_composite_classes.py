"""Action service — composite classes.
Combine a function action, a class action, and a bound service method.
The service can also define its own methods using these actions."""

import asyncio
from typing import assert_type

from fastsprout.actions import Action, action
from fastsprout.core import BaseSchema, Field


class Document(BaseSchema):
    content: Field[str]


class SignedDocument(BaseSchema):
    content: Field[bytes]
    signature: Field[str]


@action
async def render_document(document: Document) -> bytes:
    return document.content.encode()


class SignDocument(Action[bytes, SignedDocument]):
    async def __call__(self, content: bytes) -> SignedDocument:
        return SignedDocument(
            content=content,
            signature=f"signed:{len(content)}",
        )


@action
class DocumentVerifier:
    async def verify(self, document: SignedDocument) -> bool:
        return document.signature == f"signed:{len(document.content)}"


verifier = DocumentVerifier()


@action
class DocumentService:
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
    assert_type(content, bytes)

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
