import asyncio

import pytest

from fastsprout.core.types import LazyAwait


async def test_lazy_await_magic_attrs_error():
    # given
    async def func():
        await asyncio.sleep(0)

    # when
    lazy_await = LazyAwait(func)
    # then

    with pytest.raises(AttributeError):
        _ = lazy_await.__magic__


async def test_lazy_await_magic_attrs_sync():
    # given

    async def func():
        await asyncio.sleep(0)

    func._sync_call = lambda: None  # pyright: ignore[reportFunctionMemberAccess]

    # when
    lazy_await = LazyAwait(func)
    # then
    lazy_await._sync_call()


async def test_lazy_await_magic_attrs_async():
    # given

    async def func():
        await asyncio.sleep(0)

    func._async_call_sleep = asyncio.sleep  # pyright: ignore[reportFunctionMemberAccess]

    # when
    lazy_await = LazyAwait(func)
    # then
    with pytest.raises(AttributeError):
        await lazy_await._async_call_sleep(0)


async def test_lazy_await_repr():
    # given

    async def func():
        await asyncio.sleep(0)

    # when
    lazy_await = LazyAwait(func)
    # then
    assert repr(lazy_await) == "<LazyAwait pending>"
    await lazy_await
    assert repr(lazy_await) == "<LazyAwait None>"


async def test_lazy_await_resolves_awaitable_attr():
    # given
    class Target:
        async def value(self) -> int:
            await asyncio.sleep(0)
            return 1

    async def func() -> Target:
        return Target()

    # when
    lazy_await = LazyAwait(func)
    # then
    assert await lazy_await.value() == 1


async def test_lazy_await_resolves_sync_attr():
    # given
    class Target:
        def value(self) -> int:
            return 1

    async def func() -> Target:
        return Target()

    # when
    lazy_await = LazyAwait(func)
    # then
    assert await lazy_await.value() == 1


async def test_lazy_await_resolves_chained_lazy_attr():
    # given
    class Target:
        def value(self) -> LazyAwait[int]:
            async def inner() -> int:
                return 1

            return LazyAwait(inner)

    async def func() -> Target:
        return Target()

    # when
    lazy_await = LazyAwait(func)
    # then
    assert await lazy_await.value() == 1
