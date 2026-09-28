import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from fastsprout.data.types.callable import AnyCallable
from fastsprout.data.utils.callable import (
    resolve_any_callable,
    resolve_callable_to_sync,
)
from tests.fastsprout.data.conftest import ANY_CALLABLES, ANY_EMPTY_CALLABLES


@pytest.mark.parametrize(
    "callable",
    ANY_CALLABLES,
)
async def test_resolve_any_callable(callable: AnyCallable[..., Any]):
    # given
    # when
    resolved_callable = resolve_any_callable(callable)
    # then
    await resolved_callable(None)


@pytest.mark.parametrize(
    "callable",
    ANY_EMPTY_CALLABLES,
)
async def test_resolve_any_callable_empty(
    callable: AnyCallable[..., Any],
):
    # given
    # when
    resolved_callable: Callable[..., Awaitable[Awaitable[Any]]] = (
        resolve_any_callable(callable)
    )
    # then
    await resolved_callable()


@pytest.mark.parametrize(
    "callable",
    ANY_CALLABLES,
)
async def test_resolve_callable_to_sync(callable: AnyCallable[..., Any]):
    # given
    # when
    resolved_callable = resolve_callable_to_sync(callable)
    # then
    resolved_callable(None)


@pytest.mark.parametrize(
    "callable",
    ANY_EMPTY_CALLABLES,
)
async def test_resolve_callable_to_sync_empty(
    callable: AnyCallable[..., Any],
):
    # given
    # when
    resolved_callable: Callable[..., Any] = resolve_callable_to_sync(callable)
    # then
    resolved_callable()


async def test_resolve_callable_to_sync_runtime_error():
    # given
    async def callable():
        raise RuntimeError

    loop = asyncio.new_event_loop()
    # when
    resolved_callable = resolve_callable_to_sync(callable, loop=loop)
    loop.stop()
    # then
    with pytest.raises(RuntimeError):
        resolved_callable()
