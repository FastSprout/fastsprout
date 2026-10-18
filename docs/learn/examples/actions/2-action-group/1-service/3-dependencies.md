# 3. Dependencies

<!-- example-source: examples/actions/02_action_group/01_service/03_dependencies.py -->

Use actions and selected service methods as dependencies.
Service dependencies run before each public action. A function decorated
with @action exposes .dependency as a shortcut for Depends(action).
Exceptions stop the operation.

## Source

```python
"""Use actions and selected service methods as dependencies.
Service dependencies run before each public action. A function decorated
with @action exposes .dependency as a shortcut for Depends(action).
Exceptions stop the operation.
"""

import asyncio

from fastsprout.actions import Action, Service, action
from fastsprout.core import BaseSchema, Depends, Field


class Document(BaseSchema):
    content: Field[str]


class CheckContent(Action[Document, Document]):
    async def __call__(self, document: Document) -> Document:
        if not document.content.strip():
            raise ValueError("Document content is required")
        print("Content checked:", document.content)
        return document


@action
async def check_access(document: Document) -> None:
    print("Access checked:", document.content)


class DocumentChecks(Service):
    access = check_access


checks = DocumentChecks()
check_content = CheckContent()


class Documents(Service):
    dependencies = (checks.access.dependency, Depends(check_content))

    async def publish(self, document: Document) -> Document:
        print("Published:", document.content)
        return document


@action(dependencies=[Depends(checks.access), Depends(check_content)])
async def archive(document: Document) -> Document:
    print("Archived:", document.content)
    return document


async def main() -> None:
    documents = Documents()
    await documents.publish(Document(content="Invoice"))
    await documents.publish(Document(content="Receipt"))
    await archive(Document(content="Invoice"))
    try:
        await documents.publish(Document(content=""))
    except ValueError as error:
        print("Rejected:", error)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Access checked: Invoice
Content checked: Invoice
Published: Invoice
Access checked: Receipt
Content checked: Receipt
Published: Receipt
Access checked: Invoice
Content checked: Invoice
Archived: Invoice
Access checked:
Rejected: Document content is required
```
