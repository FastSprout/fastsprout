"""Action service — standard."""

import asyncio
from typing import assert_type

from fastsprout.actions import Service
from fastsprout.core import BaseSchema, Depends, Field


class Document(BaseSchema):
    content: Field[str]


class SignedDocument(BaseSchema):
    content: Field[bytes]
    signature: Field[str]


class DocumentRenderer:
    async def render(self, document: Document) -> bytes:
        return document.content.encode()


class Signer:
    async def sign(self, content: bytes) -> str:
        return f"signed:{len(content)}"


class DocumentService(Service):
    renderer: DocumentRenderer = Depends()
    signer: Signer = Depends()

    async def render(self, document: Document) -> bytes:
        return await self.renderer.render(document)

    async def sign(self, document: Document) -> SignedDocument:
        content = await self.render(document)

        return SignedDocument(
            content=content,
            signature=await self.signer.sign(content),
        )


async def main() -> None:
    documents = DocumentService()
    document = Document(content="FastSprout")

    content = await documents.render(document)
    assert_type(content, bytes)

    signed = await documents.sign(document)
    assert_type(signed, SignedDocument)
    print(signed)


if __name__ == "__main__":
    asyncio.run(main())
