"""Compose three typed actions in a linear workflow.
Each result becomes the next action input, including the rendered document."""

import asyncio

from fastsprout.actions import Workflow, action
from fastsprout.core import BaseSchema


class Document(BaseSchema):
    content: str


class RenderedDocument(BaseSchema):
    content: bytes


@action
async def parse(document: Document) -> Document:
    return Document(content=document.content.strip())


@action
async def validate(document: Document) -> Document:
    if not document.content:
        raise ValueError("Document is empty")

    return document


@action
async def render(document: Document) -> RenderedDocument:
    return RenderedDocument(content=document.content.encode())


workflow = Workflow(parse).then(validate).then(render)


async def main() -> None:
    async for result in workflow(Document(content="FastSprout")):
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
