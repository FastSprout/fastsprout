from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Hashable,
)
from contextlib import aclosing
from copy import deepcopy
from functools import wraps
from typing import Any

from fastsprout.core import lazy_await
from fastsprout.core.types import AnyIterable, LazyAwait
from fastsprout.core.types.protocols.ables import Addable, RichComparisonable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.protocols import AsyncCommonStreamable
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    PredicateCallable,
    ReducerCallable,
    Valuable,
)
from fastsprout.data.utils.callable import resolve_any_callable
from fastsprout.data.utils.iterable import chunked, resolve_any_iterable

__all__ = ["BaseCommonStream"]


class BaseCommonStream[T: Valuable | Entitieable]:
    @staticmethod
    def as_stream[S: Valuable | Entitieable, **P](
        function: Callable[P, AsyncIterable[S]],
    ) -> Callable[P, AsyncCommonStreamable[S]]:
        @wraps(function)
        def call(*args: P.args, **kwargs: P.kwargs) -> BaseCommonStream[S]:
            return BaseCommonStream(function(*args, **kwargs))

        return call

    def __init__(self, values: AnyIterable[T]) -> None:
        self.values: AsyncIterable[T] = resolve_any_iterable(values)

    def __aiter__(self) -> AsyncIterator[T]:
        return aiter(self.values)

    def to_list(self) -> LazyAwait[list[T]]:
        async def collect() -> list[T]:
            buffer: list[T] = []
            async with aclosing(resolve_any_iterable(self)) as source:
                async for item in source:
                    buffer.append(item)
            return buffer

        return LazyAwait(collect)

    @lazy_await
    async def to_set(self) -> set[T]:
        buffer: set[T] = set()
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                buffer.add(item)
        return buffer

    @lazy_await
    async def to_dict[K: Hashable, V](
        self,
        key: GetterCallable[T, K],
        value: GetterCallable[T, V],
    ) -> dict[K, V]:
        resolved_key = resolve_any_callable(key)
        resolved_value = resolve_any_callable(value)
        buffer: dict[K, V] = {}
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                buffer[await resolved_key(item)] = await resolved_value(item)
        return buffer

    def chunked(
        self, size: int = DEFAULT_ITERATION_CHUNK_SIZE
    ) -> AsyncIterator[list[T]]:
        return chunked(self, size)

    @lazy_await
    async def group_by[K: Hashable](
        self, key: GetterCallable[T, K]
    ) -> dict[K, list[T]]:
        resolved_key = resolve_any_callable(key)
        buffer: dict[K, list[T]] = {}
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                buffer.setdefault(await resolved_key(item), []).append(item)
        return buffer

    @lazy_await
    async def for_each(self, consumer: ConsumerCallable[T]) -> None:
        resolved_consumer = resolve_any_callable(consumer)
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                await resolved_consumer(item)

    @lazy_await
    async def reduce[R](self, reducer: ReducerCallable[T, R], initial: R) -> R:
        copied_initial = deepcopy(initial)
        resolved_reducer = resolve_any_callable(reducer)
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                copied_initial = await resolved_reducer(item, copied_initial)
        return copied_initial

    @lazy_await
    async def count(self) -> int:
        number = 0
        async with aclosing(resolve_any_iterable(self)) as source:
            async for _ in source:
                number += 1
        return number

    @lazy_await
    async def first(self) -> T | None:
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                return item
        return None

    @lazy_await
    async def all(self, predicate: PredicateCallable[T]):
        resolved_predicate = resolve_any_callable(predicate)
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                if await resolved_predicate(item):
                    pass
                else:
                    return False
        return True

    @lazy_await
    async def any(self, predicate: PredicateCallable[T]) -> bool:
        resolved_predicate = resolve_any_callable(predicate)
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                if await resolved_predicate(item):
                    return True
        return False

    @lazy_await
    async def sum_by[R: Addable](self, key: GetterCallable[T, R]) -> R | None:
        resolved_key = resolve_any_callable(key)
        buffer: R | None = None
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                if buffer is None:
                    buffer = await resolved_key(item)
                else:
                    buffer += await resolved_key(item)
        return buffer

    @lazy_await
    async def min[K: RichComparisonable[Any]](
        self, key: GetterCallable[T, K]
    ) -> T | None:
        resolved_key = resolve_any_callable(key)
        buffer_k: K | None = None
        buffer_t: T | None = None
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                k = await resolved_key(item)
                if buffer_k is None or (buffer_k is not None and k < buffer_k):  # pyright: ignore[reportOperatorIssue]
                    buffer_k = k
                    buffer_t = item
        return buffer_t

    @lazy_await
    async def max[K](self, key: GetterCallable[T, K]) -> T | None:
        resolved_key = resolve_any_callable(key)
        buffer_k: K | None = None
        buffer_t: T | None = None
        async with aclosing(resolve_any_iterable(self)) as source:
            async for item in source:
                k = await resolved_key(item)
                if buffer_k is None or (buffer_k is not None and k > buffer_k):  # pyright: ignore[reportOperatorIssue]
                    buffer_k = k
                    buffer_t = item
        return buffer_t
