import pytest

from fastsprout.core import hidden_lazy_await, lazy_await
from fastsprout.core.types import AnyCallable, AnyIterable

__all__ = ["ANY_CALLABLES", "ANY_EMPTY_CALLABLES", "ANY_ITERABLES"]


async def async_range(n: int):
    for i in range(n):
        yield i


@hidden_lazy_await  # pyright: ignore[reportArgumentType]
async def hidden_lazy_await_generator(n: int):
    for i in range(n):
        yield i


@lazy_await  # pyright: ignore[reportArgumentType]
async def lazy_await_generator(n: int):
    for i in range(n):
        yield i


ANY_ITERABLES: list[AnyIterable] = [
    range(10),
    (x for x in range(0)),
    filter(str, range(10)),
    map(str, range(10)),
    (x async for x in async_range(10)),  # type: ignore
    (x async for x in lazy_await_generator(10)),  # type: ignore
    (x async for x in hidden_lazy_await_generator(10)),  # type: ignore
]


async def async_func(x):
    return x


async def async_empty_lambda():
    return None


ANY_CALLABLES: list[AnyCallable] = [
    lambda x: x,
    async_func,
]


ANY_EMPTY_CALLABLES: list[AnyCallable] = [
    lambda: None,
    async_empty_lambda,
]


@pytest.fixture()
def any_iterables():
    return ANY_ITERABLES


@pytest.fixture()
def any_callables():
    return ANY_CALLABLES


@pytest.fixture()
def any_empty_callables():
    return ANY_EMPTY_CALLABLES
