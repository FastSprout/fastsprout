# 1. Base Action

<!-- example-source: examples/core/03_action/01_base_action.py -->

BaseAction — single typed result. Class and function styles.

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

    print(await Greet()(payload))
    print(await greet(payload))


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
message='hello, world'
message='hello, world'
```
