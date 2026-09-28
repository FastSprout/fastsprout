# 7. Action Sequence

<!-- example-source: examples/core/07_action_sequence.py -->

`BaseSequenceAction` returns an eager sequence such as a list or tuple. The class and function versions each produce three greeting schemas before the caller iterates them.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/07_action_sequence.py
```

## Source

```python
"""BaseSequenceAction — eager collection (list/tuple). Class and function styles."""

import asyncio
from collections.abc import Sequence

from fastsprout.core.action import BaseSequenceAction
from fastsprout.core.fields import Field
from fastsprout.core.schema import BaseSchema


class GreetBatchIn(BaseSchema):
    name: Field[str]
    times: Field[int]


class GreetOut(BaseSchema):
    message: Field[str]


class GreetBatch(BaseSequenceAction[GreetBatchIn, GreetOut]):
    async def __call__(self, payload: GreetBatchIn, /) -> Sequence[GreetOut]:
        return [
            GreetOut(message=f"hello, {payload.name} #{i}")
            for i in range(payload.times)
        ]


async def greet_batch(payload: GreetBatchIn, /) -> Sequence[GreetOut]:
    return [
        GreetOut(message=f"hello, {payload.name} #{i}")
        for i in range(payload.times)
    ]


async def main() -> None:
    payload = GreetBatchIn(name="world", times=3)

    assert isinstance(GreetBatch(), BaseSequenceAction)
    assert isinstance(greet_batch, BaseSequenceAction)

    print([g.message for g in await GreetBatch()(payload)])
    print([g.message for g in await greet_batch(payload)])


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

The same list is printed twice, once for each action form:

```text
['hello, world #0', 'hello, world #1', 'hello, world #2']
['hello, world #0', 'hello, world #1', 'hello, world #2']
```
