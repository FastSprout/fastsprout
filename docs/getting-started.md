# Getting Started

Install FastSprout with Python 3.12, 3.13, or 3.14:

```bash
pip install fastsprout
```

The core package includes schemas, fields, actions, and DTOs. Use the optional
`data-sql` and `events` extras when you need those integrations.

## Your first action

This example defines an input schema, an output schema, and a class implementing
`BaseAction`. The source lives in [`docs_src/quickstart.py`](https://github.com/FastSprout/fastsprout/blob/development/docs_src/quickstart.py)
so it can be run and checked independently of this page.

<!-- example-source: docs_src/quickstart.py -->

```python
"""A runnable typed action for the Getting Started guide."""

import asyncio

from fastsprout.core import BaseAction, BaseSchema, Field


class GreetingInput(BaseSchema):
    name: Field[str]


class Greeting(BaseSchema):
    message: Field[str]


class Greet(BaseAction[GreetingInput, Greeting]):
    async def __call__(self, payload: GreetingInput, /) -> Greeting:
        return Greeting(message=f"Hello, {payload.name}!")


async def main() -> None:
    greeting = await Greet()(GreetingInput(name="world"))
    print(greeting.message)


if __name__ == "__main__":
    asyncio.run(main())
```

Run it from the repository root:

```bash
uv run python docs_src/quickstart.py
```

## Result

```text
Hello, world!
```

An async function can implement the same action protocol; see the
[class and function examples](learn/examples/core/6-action.md).

## Next steps

- Explore [schemas, fields, DTOs, and actions](features.md).
- Try the [runnable examples](learn/examples/index.md) for core, data, and events.
- [Publish and subscribe to an event](guide/events.md).
- Browse the [API reference](api/index.md) for the exported Python interfaces.
