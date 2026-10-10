"""Expand a sequence action into an async stream of documents.
The next action renders each document separately.
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


async def load(request: DocumentRequest) -> Sequence[Document]:
    return tuple(Document(content=text) for text in request.contents)


async def render(document: Document) -> RenderedDocument:
    return RenderedDocument(content=document.content.encode())


sequence: BaseSequenceAction[DocumentRequest, Document] = load
workflow = Workflow(sequence).then(render)


async def main() -> None:
    request = DocumentRequest(contents=("Guide", "Reference"))
    async for document in workflow(request):
        print(document)


if __name__ == "__main__":
    asyncio.run(main())
