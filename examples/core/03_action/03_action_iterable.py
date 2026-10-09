"""Return greetings lazily from a class action or an async function.

Both callables satisfy BaseIterableAction. Awaiting either one returns a
synchronous iterable; each GreetOut is created only when the caller iterates.
"""

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

    print([g.message for g in await GreetBatch()(payload)])
    print([g.message for g in await greet_batch(payload)])


if __name__ == "__main__":
    asyncio.run(main())
