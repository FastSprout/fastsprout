import asyncio
from collections.abc import AsyncIterable, AsyncIterator

from fastsprout.core.decorators import hidden_lazy_await, lazy_await
from fastsprout.core.types import LazyAwait


async def test_lazy_await():
    # given
    @lazy_await
    async def test_await() -> int:
        await asyncio.sleep(0)
        return 1

    # when
    result = test_await()
    # then
    assert isinstance(result, LazyAwait)
    assert isinstance(await result, int)
    assert isinstance(result, LazyAwait)
    assert isinstance(await result, int)


async def test_hidden_lazy_await():
    # given
    @hidden_lazy_await
    async def test_await() -> int:
        await asyncio.sleep(0)
        return 1

    # when
    result = test_await()
    # then
    assert isinstance(result, LazyAwait)
    assert isinstance(await result, int)
    assert isinstance(result, LazyAwait)
    assert isinstance(await result, int)


async def test_lazy_await_gen():
    # given
    @lazy_await  # pyright: ignore[reportArgumentType]
    async def test_asyncgen():
        for i in range(10):
            yield i

    # when
    result = test_asyncgen()
    # then
    assert isinstance(result, LazyAwait)
    assert not isinstance(result, AsyncIterator)
    async for _ in result:
        pass
    assert isinstance(result, LazyAwait)
    assert not isinstance(result, AsyncIterator)


async def test_hidden_lazy_await_gen():
    # given
    @hidden_lazy_await  # pyright: ignore[reportArgumentType]
    async def test_asyncgen():
        for i in range(10):
            yield i

    # when
    result: AsyncIterable[int] = test_asyncgen()
    # then
    assert isinstance(result, LazyAwait)
    assert not isinstance(result, AsyncIterator)
    async for _ in result:
        pass
    assert isinstance(result, LazyAwait)
    assert not isinstance(result, AsyncIterator)
