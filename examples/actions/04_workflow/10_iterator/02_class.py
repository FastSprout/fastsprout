"""Nest workflows built from a BaseIteratorAction class.
Each document passes through the nested workflow to a rendering action.
"""

import asyncio
from collections.abc import AsyncIterator

from fastsprout.actions import Workflow
from fastsprout.core import BaseSchema
from fastsprout.core.action import BaseIteratorAction


class DocumentRequest(BaseSchema):
    contents: tuple[str, ...]


class Document(BaseSchema):
    content: str


class RenderedDocument(BaseSchema):
    content: bytes


class LoadDocuments(BaseIteratorAction[DocumentRequest, Document]):
    async def __call__(
        self, payload: DocumentRequest
    ) -> AsyncIterator[Document]:
        for text in payload.contents:
            await asyncio.sleep(0)
            print("Reading:", text)
            yield Document(content=text)


class Render:
    async def __call__(self, document: Document) -> RenderedDocument:
        return RenderedDocument(content=document.content.encode())


load_documents = Workflow(LoadDocuments())
workflow = Workflow(load_documents).then(Render())


async def main() -> None:
    request = DocumentRequest(contents=("Guide", "Reference"))
    documents = workflow(request)
    print("Stream ready; documents have not been read yet")
    async for document in documents:
        print(document)


if __name__ == "__main__":
    asyncio.run(main())
