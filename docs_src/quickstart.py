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
