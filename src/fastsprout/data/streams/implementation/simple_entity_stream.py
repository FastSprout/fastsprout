from collections.abc import AsyncIterable
from operator import itemgetter
from typing import Any, cast

from fastsprout.core import hidden_lazy_await
from fastsprout.core.types import AnyIterable
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.implementation.base_common_stream import (
    BaseCommonStream,
)
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    HashableAndValuable,
    MapperCallable,
    PredicateCallable,
)
from fastsprout.data.utils.callable import resolve_any_callable
from fastsprout.data.utils.iterable import achain

from ..protocols import AsyncEntityStream
from .simple_value_stream import SimpleAsyncValueStream

__all__ = ["SimpleAsyncEntityStream"]


class SimpleAsyncEntityStream[E: Entitieable](
    BaseCommonStream[E], AsyncEntityStream[E]
):
    @hidden_lazy_await
    async def concat(self, *others: "AsyncEntityStream[E] | AnyIterable[E]"):
        return SimpleAsyncEntityStream[E](
            achain(self, *(cast(tuple[AsyncIterable, ...], others)))
        )

    @hidden_lazy_await
    async def map[R: Entitieable](self, mapper: MapperCallable[E, R]):
        resolved_mapper = resolve_any_callable(mapper)

        async def gen():
            async for item in self:
                yield (await resolved_mapper(item))

        return SimpleAsyncEntityStream[R](gen())

    @hidden_lazy_await
    async def sort[R: RichComparisonable[Any]](
        self,
        key: GetterCallable[E, R],
        reverse: bool = False,
    ):
        resolved_key = resolve_any_callable(key)
        buffer = await self.to_list()

        decorated = [(await resolved_key(item), item) for item in buffer]
        decorated.sort(key=itemgetter(0), reverse=reverse)
        return SimpleAsyncEntityStream[E]([item for _, item in decorated])

    @hidden_lazy_await
    async def filter(self, predicate: PredicateCallable[E]):
        resolved_predicate = resolve_any_callable(predicate)

        async def gen():
            async for item in self:
                keep = await resolved_predicate(item)
                if keep:
                    yield item

        return SimpleAsyncEntityStream[E](gen())

    @hidden_lazy_await
    async def distinct(self):
        async def gen():
            seen = []
            async for item in self:
                if item in seen:
                    continue
                seen.append(item)
                yield item

        return SimpleAsyncEntityStream[E](gen())

    @hidden_lazy_await
    async def peek(self, consumer: ConsumerCallable[E]):
        resolved_consumer = resolve_any_callable(consumer)

        async def gen():
            async for item in self:
                await resolved_consumer(item)
                yield item

        return SimpleAsyncEntityStream[E](gen())

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

        return SimpleAsyncEntityStream[E](gen())

    @hidden_lazy_await
    async def drop(self, n: int):
        async def gen():
            remaining = n
            async for item in self:
                if remaining > 0:
                    remaining -= 1
                    continue
                yield item

        return SimpleAsyncEntityStream[E](gen())

    @hidden_lazy_await
    async def take_while(self, predicate: PredicateCallable[E]):
        resolved_predicate = resolve_any_callable(predicate)

        async def gen():
            async for item in self:
                if not await resolved_predicate(item):
                    return
                yield item

        return SimpleAsyncEntityStream[E](gen())

    @hidden_lazy_await
    async def drop_while(self, predicate: PredicateCallable[E]):
        resolved_predicate = resolve_any_callable(predicate)

        async def gen():
            dropping = True
            async for item in self:
                if dropping:
                    if await resolved_predicate(item):
                        continue
                    dropping = False
                yield item

        return SimpleAsyncEntityStream[E](gen())

    @hidden_lazy_await
    async def to_values[K: HashableAndValuable](
        self, mapper: MapperCallable[E, K]
    ):
        resolved_mapper = resolve_any_callable(mapper)

        async def gen():
            async for item in self:
                yield await resolved_mapper(item)

        return SimpleAsyncValueStream[K](gen())
