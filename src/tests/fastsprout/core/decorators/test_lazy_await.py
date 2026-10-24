import asyncio
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import aclosing
from typing import assert_type

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
    emitted: list[int] = []
    closed: list[bool] = []

    @lazy_await
    async def test_asyncgen() -> AsyncGenerator[int, None]:
        try:
            for i in range(10):
                emitted.append(i)
                yield i
        finally:
            closed.append(True)

    # when
    result = test_asyncgen()
    # then
    assert isinstance(result, LazyAwait)
    assert not isinstance(result, AsyncIterator)
    assert emitted == []
    async with aclosing(result.__aiter__()) as iterator:
        value = await anext(iterator)
        assert_type(value, int)
        assert value == 0
        assert emitted == [0]
    assert closed == [True]
    assert isinstance(result, LazyAwait)
    assert not isinstance(result, AsyncIterator)


async def test_hidden_lazy_await_gen():
    # given
    @hidden_lazy_await
    async def test_asyncgen() -> AsyncGenerator[int, None]:
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
