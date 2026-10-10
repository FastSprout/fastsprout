"""Use a workflow as an action inside another workflow.
The preparation and rendering workflows keep their own input and output types.
"""

import asyncio

from fastsprout.actions import Workflow, action
from fastsprout.core import Schema, dataclass, typed_fields
from fastsprout.core.action import BaseIteratorAction


@dataclass
class Document(Schema):
    content: str


@typed_fields
class RenderedDocument(Schema):
    content: bytes

    def __init__(self, content: bytes) -> None:
        self.content = content


@action
async def normalize(document: Document) -> Document:
    return Document(content=document.content.strip())


@action
async def validate(document: Document) -> Document:
    if not document.content:
        raise ValueError("Document is empty")
    return document


@action
async def render(document: Document) -> RenderedDocument:
    return RenderedDocument(content=document.content.encode())


prepare = Workflow(normalize).then(validate)
renderer = Workflow(render)
publish: BaseIteratorAction[Document, RenderedDocument] = Workflow(
    prepare
).then(renderer)


async def main() -> None:
    async for document in publish(Document(content="  FastSprout  ")):
        print(document.content)


if __name__ == "__main__":
    asyncio.run(main())
