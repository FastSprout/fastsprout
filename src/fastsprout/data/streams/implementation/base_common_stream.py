from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Hashable,
)
from copy import deepcopy
from typing import Any

from fastsprout.core import lazy_await
from fastsprout.core.types import AnyIterable
from fastsprout.core.types.protocols.ables import Addable, RichComparisonable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import Entitieable
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    PredicateCallable,
    ReducerCallable,
    Valuable,
)
from fastsprout.data.utils.callable import resolve_any_callable
from fastsprout.data.utils.iterable import resolve_any_iterable

__all__ = ["BaseCommonStream"]


class BaseCommonStream[T: Valuable | Entitieable]:
    def __init__(self, values: AnyIterable[T]) -> None:
        self.__values: AsyncIterable[T] = resolve_any_iterable(values)

    def __aiter__(self) -> AsyncIterator[T]:
        async def wrapper() -> AsyncIterator[T]:
            async for item in self.__values:
                yield item

        return wrapper()

    @lazy_await
    async def to_list(self) -> list[T]:
        buffer: list[T] = []
        async for item in self:
            buffer.append(item)
        return buffer

    @lazy_await
    async def to_set(self) -> set[T]:
        buffer: set[T] = set()
        async for item in self:
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
        async for item in self:
            buffer[await resolved_key(item)] = await resolved_value(item)
        return buffer

    async def chunked(
        self, size: int = DEFAULT_ITERATION_CHUNK_SIZE
    ) -> AsyncIterator[list[T]]:
        buffer: list[T] = []

        async for item in self:
            buffer.append(item)
            if len(buffer) == size:
                yield buffer
                buffer = []

        if buffer:
            yield buffer

    @lazy_await
    async def group_by[K: Hashable](
        self, key: GetterCallable[T, K]
    ) -> dict[K, list[T]]:
        resolved_key = resolve_any_callable(key)
        buffer: dict[K, list[T]] = {}
        async for item in self:
            buffer.setdefault(await resolved_key(item), []).append(item)
        return buffer

    @lazy_await
    async def for_each(self, consumer: ConsumerCallable[T]) -> None:
        resolved_consumer = resolve_any_callable(consumer)
        async for item in self:
            await resolved_consumer(item)

    @lazy_await
    async def reduce[R](self, reducer: ReducerCallable[T, R], initial: R) -> R:
        copied_initial = deepcopy(initial)
        resolved_reducer = resolve_any_callable(reducer)
        async for item in self:
            copied_initial = await resolved_reducer(item, copied_initial)
        return copied_initial

    @lazy_await
    async def count(self) -> int:
        number = 0
        async for _ in self:
            number += 1
        return number

    @lazy_await
    async def first(self) -> T | None:
        async for item in self:
            return item
        return None

    @lazy_await
    async def all(self, predicate: PredicateCallable[T]):
        resolved_predicate = resolve_any_callable(predicate)
        async for item in self:
            if await resolved_predicate(item):
                pass
            else:
                return False
        return True

    @lazy_await
    async def any(self, predicate: PredicateCallable[T]) -> bool:
        resolved_predicate = resolve_any_callable(predicate)
        async for item in self:
            if await resolved_predicate(item):
                return True
        return False

    @lazy_await
    async def sum_by[R: Addable](self, key: GetterCallable[T, R]) -> R | None:
        resolved_key = resolve_any_callable(key)
        buffer: R | None = None
        async for item in self:
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
        async for item in self:
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
        async for item in self:
            k = await resolved_key(item)
            if buffer_k is None or (buffer_k is not None and k > buffer_k):  # pyright: ignore[reportOperatorIssue]
                buffer_k = k
                buffer_t = item
        return buffer_t
