from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from collections.abc import Iterable as RuntimeIterable
from contextlib import aclosing, nullcontext

from .protocols.ables import ACloseable, AIterable, Iterable

__all__ = ["AnyIterable", "Chunk", "resolve_any_iterable"]

type AnyIterable[S] = Iterable[S] | AIterable[S]


async def resolve_any_iterable[S](
    iterable: AnyIterable[S],
) -> AsyncGenerator[S, None]:
    if isinstance(iterable, AsyncIterable):
        iterator = aiter(iterable)
        async with (
            aclosing(iterator)
            if isinstance(iterator, ACloseable)
            else nullcontext(iterator)
        ):
            async for item in iterator:
                yield item
    elif isinstance(iterable, RuntimeIterable):
        for item in iterable:
            yield item
    else:
        raise TypeError("Expected an iterable or async iterable")


class Chunk[T](AsyncIterable[T]):
    """A lazy input batch that dependencies may replace."""

    def __init__(self, source: AnyIterable[T]) -> None:
        self.source: AnyIterable[T] = source

    def __aiter__(self) -> AsyncIterator[T]:
        return resolve_any_iterable(self.source)
