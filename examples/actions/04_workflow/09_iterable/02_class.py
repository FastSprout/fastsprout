"""Compose a IterableActionable class without collecting its generator.
The workflow reads and renders documents one at a time using async for.
"""

import asyncio
from collections.abc import Iterable, Iterator

from fastsprout.actions import Workflow
from fastsprout.core import BaseSchema
from fastsprout.core.action import IterableActionable


class DocumentRequest(BaseSchema):
    contents: tuple[str, ...]


class Document(BaseSchema):
    content: str


class RenderedDocument(BaseSchema):
    content: bytes


class LoadDocuments(IterableActionable[DocumentRequest, Document]):
    def documents(self, payload: DocumentRequest) -> Iterator[Document]:
        for text in payload.contents:
            print("Reading:", text)
            yield Document(content=text)

    async def __call__(self, payload: DocumentRequest) -> Iterable[Document]:
        return self.documents(payload)


class Render:
    async def __call__(self, document: Document) -> RenderedDocument:
        return RenderedDocument(content=document.content.encode())


workflow = Workflow(LoadDocuments()).then(Render())


async def main() -> None:
    request = DocumentRequest(contents=("Guide", "Reference"))
    documents = workflow(request)
    print("Stream ready; documents have not been read yet")
    async for document in documents:
        print(document)


if __name__ == "__main__":
    asyncio.run(main())
