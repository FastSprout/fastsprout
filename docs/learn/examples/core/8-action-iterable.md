# 8. Action Iterable

<!-- example-source: examples/core/08_action_iterable.py -->

`BaseIterableAction` returns a synchronous iterable. Here both actions return generators, so greeting objects are produced as the caller consumes the returned iterable.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/08_action_iterable.py
```

## Source

```python
"""BaseIterableAction — lazy sync iterable (generator). Class and function styles."""

import asyncio
from collections.abc import Iterable

from fastsprout.core.action import BaseIterableAction
from fastsprout.core.fields import Field
from fastsprout.core.schema import BaseSchema


class GreetBatchIn(BaseSchema):
    name: Field[str]
    times: Field[int]


class GreetOut(BaseSchema):
    message: Field[str]


class GreetBatch(BaseIterableAction[GreetBatchIn, GreetOut]):
    async def __call__(self, payload: GreetBatchIn, /) -> Iterable[GreetOut]:
        return (
            GreetOut(message=f"hello, {payload.name} #{i}")
            for i in range(payload.times)
        )


async def greet_batch(payload: GreetBatchIn, /) -> Iterable[GreetOut]:
    return (
        GreetOut(message=f"hello, {payload.name} #{i}")
        for i in range(payload.times)
    )


async def main() -> None:
    payload = GreetBatchIn(name="world", times=3)

    assert isinstance(GreetBatch(), BaseIterableAction)
    assert isinstance(greet_batch, BaseIterableAction)

    print([g.message for g in await GreetBatch()(payload)])
    print([g.message for g in await greet_batch(payload)])


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

Consuming either generator yields the same three messages:

```text
['hello, world #0', 'hello, world #1', 'hello, world #2']
['hello, world #0', 'hello, world #1', 'hello, world #2']
```
