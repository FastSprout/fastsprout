import asyncio
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    Callable,
    Hashable,
)
from contextlib import aclosing
from inspect import isawaitable, iscoroutinefunction

from fastsprout.data.streams.context import in_join_context
from fastsprout.data.streams.protocols.joined_stream import (
    AsyncJoinedStream,
    JoinKey,
)
from fastsprout.data.utils.iterable import resolve_any_iterable

__all__ = ["JoinKey", "JoinedStream"]


async def resolve_key[T](callback: JoinKey[T], item: T) -> Hashable:
    result = (
        callback(item)
        if iscoroutinefunction(callback)
        else await asyncio.to_thread(callback, item)
    )
    return await result if isawaitable(result) else result


class JoinedStream[*Ts](AsyncJoinedStream[*Ts]):
    """Lazy inner joins producing flat, statically typed tuples.

    Each step buffers its right source in a hash index, then streams the
    left rows in order. Duplicate keys produce every matching pair in
    right-source order. Keys must be hashable; None is an ordinary key.
    Plans are immutable, but replay requires replayable input sources.
    Routed sources must share one active DataR context; this is checked
    during iteration, including sources wrapped in stream transformations.
    """

    iterate: Callable[[], AsyncGenerator[tuple[*Ts], None]]

    def __init__[T](self: "JoinedStream[T]", first: AsyncIterable[T]) -> None:
        async def rows() -> AsyncGenerator[tuple[T], None]:
            async with aclosing(resolve_any_iterable(first)) as iterator:
                async for item in iterator:
                    yield (item,)

        self.iterate = rows

    @staticmethod
    def from_factory[*Rs](
        factory: Callable[[], AsyncGenerator[tuple[*Rs], None]],
    ) -> "JoinedStream[*Rs]":
        joined: JoinedStream[*Rs] = object.__new__(JoinedStream)
        joined.iterate = factory
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
            async with aclosing(resolve_any_iterable(stream)) as right:
                async for item in right:
                    index.setdefault(
                        await resolve_key(right_key, item), []
                    ).append(item)
            async with aclosing(resolve_any_iterable(self)) as left:
                async for row in left:
                    for match in index.get(
                        await resolve_key(left_key, row), ()
                    ):
                        yield (*row, match)

        return JoinedStream.from_factory(rows)

    def __aiter__(self) -> AsyncGenerator[tuple[*Ts], None]:
        """Return an iterator; close it explicitly when stopping early."""
        return in_join_context(self.iterate())

    async def to_list(self) -> list[tuple[*Ts]]:
        return [row async for row in self]
