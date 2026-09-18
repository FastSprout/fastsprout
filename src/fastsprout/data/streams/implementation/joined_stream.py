import asyncio
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Hashable,
)
from contextlib import asynccontextmanager
from inspect import isawaitable, iscoroutinefunction

from fastsprout.data.streams.context import in_join_context

__all__ = ["JoinedStream"]

type JoinKey[T] = Callable[[T], Hashable | Awaitable[Hashable]]


async def _key[T](callback: JoinKey[T], item: T) -> Hashable:
    result = (
        callback(item)
        if iscoroutinefunction(callback)
        else await asyncio.to_thread(callback, item)
    )
    return await result if isawaitable(result) else result


@asynccontextmanager
async def _iterating[T](
    source: AsyncIterable[T],
) -> AsyncIterator[AsyncIterator[T]]:
    iterator = aiter(source)
    try:
        yield iterator
    finally:
        close = getattr(iterator, "aclose", None)
        if close is not None:
            await close()


class JoinedStream[*Ts]:
    """Lazy inner joins producing flat, statically typed tuples.

    Each step buffers its right source in a hash index, then streams the
    left rows in order. Duplicate keys produce every matching pair in
    right-source order. Keys must be hashable; None is an ordinary key.
    Plans are immutable, but replay requires replayable input sources.
    Routed sources must share one active DataR context; this is checked
    during iteration, including sources wrapped in stream transformations.
    """

    _iterate: Callable[[], AsyncGenerator[tuple[*Ts], None]]

    def __init__[T](self: "JoinedStream[T]", first: AsyncIterable[T]) -> None:
        async def rows() -> AsyncGenerator[tuple[T], None]:
            async with _iterating(first) as iterator:
                async for item in iterator:
                    yield (item,)

        self._iterate = rows

    @staticmethod
    def _from_factory[*Rs](
        factory: Callable[[], AsyncGenerator[tuple[*Rs], None]],
    ) -> "JoinedStream[*Rs]":
        joined: JoinedStream[*Rs] = object.__new__(JoinedStream)
        joined._iterate = factory
        return joined

    def join[T](
        self,
        stream: AsyncIterable[T],
        *,
        on: tuple[JoinKey[tuple[*Ts]], JoinKey[T]],
    ) -> "JoinedStream[*Ts, T]":
        """Append a source, matching keys from the accumulated row and item.

        Both key functions can be synchronous or asynchronous, following
        the same callback conventions as the other data streams.
        """
        left_key, right_key = on

        async def rows() -> AsyncGenerator[tuple[*Ts, T], None]:
            index: dict[Hashable, list[T]] = {}
            async with _iterating(stream) as right:
                async for item in right:
                    index.setdefault(await _key(right_key, item), []).append(
                        item
                    )
            async with _iterating(self) as left:
                async for row in left:
                    for match in index.get(await _key(left_key, row), ()):
                        yield (*row, match)

        return JoinedStream._from_factory(rows)

    def __aiter__(self) -> AsyncGenerator[tuple[*Ts], None]:
        """Return an iterator; close it explicitly when stopping early."""
        return in_join_context(self._iterate())

    async def to_list(self) -> list[tuple[*Ts]]:
        return [row async for row in self]
