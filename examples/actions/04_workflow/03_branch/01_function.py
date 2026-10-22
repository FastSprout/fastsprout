"""Choose workflow paths by the document class returned from classify.
Each branch accepts its own input type and the workflow returns their result union."""

import asyncio

from fastsprout.actions import Workflow, action
from fastsprout.core import BaseSchema


class Document(BaseSchema):
    content: str


class TextDocument(Document): ...


class EmptyDocument(Document): ...


class IndexedDocument(BaseSchema):
    content: str


class RejectedDocument(BaseSchema):
    reason: str


@action
async def classify(
    document: Document,
) -> TextDocument | EmptyDocument:
    if document.content.strip():
        return TextDocument(content=document.content)

    return EmptyDocument(content=document.content)


@action
async def index(
    document: TextDocument,
) -> IndexedDocument:
    return IndexedDocument(
        content=document.content,
    )


@action
async def reject(
    document: EmptyDocument,
) -> RejectedDocument:
    return RejectedDocument(
        reason="Document is empty",
    )


workflow = (
    Workflow(classify).branch(TextDocument, index).branch(EmptyDocument, reject)
)


async def main() -> None:
    async for indexed in workflow(Document(content="FastSprout")):
        print(indexed)
    async for rejected in workflow(Document(content="")):
        print(rejected)


if __name__ == "__main__":
    asyncio.run(main())
