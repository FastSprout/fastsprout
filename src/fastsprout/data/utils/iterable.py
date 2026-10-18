from collections.abc import AsyncIterator
from contextlib import aclosing

from fastsprout.core.types import AnyIterable
from fastsprout.core.types.iterable import resolve_any_iterable

__all__ = ["achain", "chunked", "resolve_any_iterable"]


async def chunked[T](
    values: AnyIterable[T], size: int
) -> AsyncIterator[list[T]]:
    if size <= 0:
        raise ValueError("chunk_size must be positive")
    buffer: list[T] = []
    async with aclosing(resolve_any_iterable(values)) as source:
        async for item in source:
            buffer.append(item)
            if len(buffer) == size:
                yield buffer
                buffer = []
    if buffer:
        yield buffer


async def achain[T](*its: AnyIterable[T]) -> AsyncIterator[T]:
    for it in its:
        async for item in resolve_any_iterable(it):
            yield item
