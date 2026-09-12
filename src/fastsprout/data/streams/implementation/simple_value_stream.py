from collections.abc import (
    AsyncIterable,
    Awaitable,
    Callable,
)
from operator import itemgetter
from typing import cast

from fastsprout.core import hidden_lazy_await, lazy_await
from fastsprout.core.types import AnyIterable
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.streams.protocols import AsyncValueStream
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    MapperCallable,
    PredicateCallable,
    Valuable,
)
from fastsprout.data.utils.callable import resolve_any_callable
from fastsprout.data.utils.iterable import achain

from .base_common_stream import BaseCommonStream

__all__ = ["SimpleAsyncValueStream"]


class SimpleAsyncValueStream[T: Valuable](
    BaseCommonStream[T], AsyncValueStream[T]
):
    @hidden_lazy_await
    async def concat(self, *others: "AsyncValueStream[T] | AnyIterable[T]"):
        return SimpleAsyncValueStream[T](
            achain(self, *(cast(tuple[AsyncIterable, ...], others)))
        )

    @hidden_lazy_await
    async def map[R: Valuable](self, mapper: MapperCallable[T, R]):
        resolved_mapper = resolve_any_callable(mapper)

        async def gen():
            async for item in self:
                yield await resolved_mapper(item)

        return SimpleAsyncValueStream[R](gen())

    @hidden_lazy_await
    async def filter(self, predicate: PredicateCallable[T]):
        resolved_predicate = resolve_any_callable(predicate)

        async def gen():
            async for item in self:
                keep = await resolved_predicate(item)
                if keep:
                    yield item

        return SimpleAsyncValueStream[T](gen())

    @hidden_lazy_await
    async def distinct(self):
        async def gen():
            seen = []
            async for item in self:
                if item in seen:
                    continue
                seen.append(item)
                yield item

        return SimpleAsyncValueStream[T](gen())

    @hidden_lazy_await
    async def peek(self, consumer: ConsumerCallable[T]):
        resolved_consumer = resolve_any_callable(consumer)

        async def gen():
            async for item in self:
                await resolved_consumer(item)
                yield item

        return SimpleAsyncValueStream[T](gen())

    @hidden_lazy_await
    async def take(self, n: int):
        async def gen():
            if n <= 0:
                return
            taken = 0
            async for item in self:
                yield item
                taken += 1
                if taken >= n:
                    return

        return SimpleAsyncValueStream[T](gen())

    @hidden_lazy_await
    async def drop(self, n: int):
        async def gen():
            index = 0
            async for item in self:
                if index >= n:
                    yield item
                index += 1

        return SimpleAsyncValueStream[T](gen())

    @hidden_lazy_await
    async def take_while(self, predicate: PredicateCallable[T]):
        resolved_predicate = resolve_any_callable(predicate)

        async def gen():
            async for item in self:
                if not await resolved_predicate(item):
                    return
                yield item

        return SimpleAsyncValueStream[T](gen())

    @hidden_lazy_await
    async def drop_while(self, predicate: PredicateCallable[T]):
        resolved_predicate = resolve_any_callable(predicate)

        async def gen():
            dropping = True
            async for item in self:
                if dropping:
                    if await resolved_predicate(item):
                        continue
                    dropping = False
                yield item

        return SimpleAsyncValueStream[T](gen())

    @hidden_lazy_await
    async def sort[R: RichComparisonable](
        self,
        key: GetterCallable[T, R] | None = None,
        reverse: bool = False,
    ):
        resolved_key: Callable[[T], Awaitable[R]] = (
            resolve_any_callable(key)
            if key
            else resolve_any_callable(lambda x: x)
        )
        buffer = await self.to_list()

        decorated = [(await resolved_key(item), item) for item in buffer]
        decorated.sort(key=itemgetter(0), reverse=reverse)
        return SimpleAsyncValueStream[T]([item for _, item in decorated])

    @lazy_await
    async def sum(self) -> T | None:
        buffer: T | None = None
        async for item in self:
            if buffer is None:
                buffer = item
            else:
                buffer += item
        return buffer
