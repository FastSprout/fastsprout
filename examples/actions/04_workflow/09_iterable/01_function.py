"""Consume a synchronous generator through an async workflow.
Each document is read and rendered before the next one is requested.
"""

import asyncio
from collections.abc import Iterable, Iterator

from fastsprout.actions import Workflow
from fastsprout.core import BaseSchema
from fastsprout.core.action import BaseIterableAction


class DocumentRequest(BaseSchema):
    contents: tuple[str, ...]


class Document(BaseSchema):
    content: str


class RenderedDocument(BaseSchema):
    content: bytes


def documents_from(request: DocumentRequest) -> Iterator[Document]:
    for text in request.contents:
        print("Reading:", text)
        yield Document(content=text)


async def load(request: DocumentRequest) -> Iterable[Document]:
    return documents_from(request)


async def render(document: Document) -> RenderedDocument:
    return RenderedDocument(content=document.content.encode())


iterable: BaseIterableAction[DocumentRequest, Document] = load
workflow = Workflow(iterable).then(render)


async def main() -> None:
    request = DocumentRequest(contents=("Guide", "Reference"))
    documents = workflow(request)
    print("Stream ready; documents have not been read yet")
    async for document in documents:
        print(document)


if __name__ == "__main__":
    asyncio.run(main())
