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
