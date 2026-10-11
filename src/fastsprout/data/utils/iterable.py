from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Iterable,
)
from contextlib import aclosing, nullcontext

from fastsprout.core.types import AnyIterable
from fastsprout.core.types.protocols.ables import ACloseable

__all__ = ["achain", "resolve_any_iterable"]


async def achain[T](*its: AnyIterable[T]) -> AsyncIterator[T]:
    for it in its:
        async for item in resolve_any_iterable(it):
            yield item


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
    elif isinstance(iterable, Iterable):
        for item in iterable:
            yield item
    else:
        raise TypeError("Expected an iterable or async iterable")
