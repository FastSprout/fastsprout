# 6. Action

<!-- example-source: examples/core/06_action.py -->

`BaseAction[Input, Output]` describes one asynchronous result. Both a callable class and an `async def` function are recognized as actions; the example calls each with the same input schema.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/06_action.py
```

## Source

```python
"""BaseAction — single typed result. Class and function styles."""

import asyncio

from fastsprout.core.action import BaseAction
from fastsprout.core.fields import Field
from fastsprout.core.schema import BaseSchema


class GreetIn(BaseSchema):
    name: Field[str]


class GreetOut(BaseSchema):
    message: Field[str]


class Greet(BaseAction[GreetIn, GreetOut]):
    async def __call__(self, payload: GreetIn, /) -> GreetOut:
        return GreetOut(message=f"hello, {payload.name}")


async def greet(payload: GreetIn, /) -> GreetOut:
    return GreetOut(message=f"hello, {payload.name}")


async def main() -> None:
    payload = GreetIn(name="world")

    assert isinstance(Greet(), BaseAction)
    assert isinstance(greet, BaseAction)

    print(await Greet()(payload))
    print(await greet(payload))


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

Both forms return the same typed output:

```text
message='hello, world'
message='hello, world'
```
