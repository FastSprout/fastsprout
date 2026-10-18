# 1. Function

<!-- example-source: examples/actions/04_workflow/02_graph/01_function.py -->

Analyze and summarize one document concurrently, then join the results.
The join action receives a typed ForkResult and returns a DocumentReport.

## Source

```python
"""Analyze and summarize one document concurrently, then join the results.
The join action receives a typed ForkResult and returns a DocumentReport."""

import asyncio

from fastsprout.actions import ForkResult, Workflow, action
from fastsprout.core import BaseSchema


class Document(BaseSchema):
    content: str


class Analysis(BaseSchema):
    words: int


class Summary(BaseSchema):
    content: str


class DocumentReport(BaseSchema):
    analysis: Analysis
    summary: Summary


@action
async def load(document: Document) -> Document:
    return document


@action
async def analyze(document: Document) -> Analysis:
    return Analysis(
        words=len(document.content.split()),
    )


@action
async def summarize(document: Document) -> Summary:
    return Summary(
        content=document.content[:20],
    )


@action
async def build_report(
    results: ForkResult[Analysis, Summary],
) -> DocumentReport:
    return DocumentReport(
        analysis=results.left,
        summary=results.right,
    )


workflow = (
    Workflow(load)
    .fork(
        analyze,
        summarize,
    )
    .join(build_report)
)


async def main() -> None:
    async for report in workflow(
        Document(content="FastSprout makes backend development simple")
    ):
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
analysis=Analysis(words=5) summary=Summary(content='FastSprout makes bac')
```
