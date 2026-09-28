# 9. Action Iterator

<!-- example-source: examples/core/09_action_iterator.py -->

`BaseIteratorAction` streams results through an async iterator. The caller uses `async for`; the class and function forms have the same output type and behavior.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/09_action_iterator.py
```

## Source

```python
"""BaseIteratorAction — async streaming (async-gen). Class and function styles."""

import asyncio
from collections.abc import AsyncIterator

from fastsprout.core.action import BaseIteratorAction
from fastsprout.core.fields import Field
from fastsprout.core.schema import BaseSchema


class GreetBatchIn(BaseSchema):
    name: Field[str]
    times: Field[int]


class GreetOut(BaseSchema):
    message: Field[str]


class GreetBatch(BaseIteratorAction[GreetBatchIn, GreetOut]):
    async def __call__(
        self, payload: GreetBatchIn, /
    ) -> AsyncIterator[GreetOut]:
        for i in range(payload.times):
            yield GreetOut(message=f"hello, {payload.name} #{i}")


async def greet_batch(payload: GreetBatchIn, /) -> AsyncIterator[GreetOut]:
    for i in range(payload.times):
        yield GreetOut(message=f"hello, {payload.name} #{i}")


async def main() -> None:
    payload = GreetBatchIn(name="world", times=3)

    assert isinstance(GreetBatch(), BaseIteratorAction)
    assert isinstance(greet_batch, BaseIteratorAction)

    print([g.message async for g in GreetBatch()(payload)])
    print([g.message async for g in greet_batch(payload)])


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

Both async iterators yield three greetings:

```text
['hello, world #0', 'hello, world #1', 'hello, world #2']
['hello, world #0', 'hello, world #1', 'hello, world #2']
```
