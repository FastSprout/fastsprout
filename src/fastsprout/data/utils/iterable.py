from collections.abc import AsyncIterator, Iterable
from typing import cast

from fastsprout.core.types import AnyIterable

__all__ = ["achain", "resolve_any_iterable"]


async def achain[T](*its: AnyIterable[T]) -> AsyncIterator[T]:
    for it in its:
        async for item in resolve_any_iterable(it):
            yield item


def resolve_any_iterable[S](iterable: AnyIterable[S]) -> AsyncIterator[S]:
    if hasattr(iterable, "__aiter__"):
        return cast(AsyncIterator[S], iterable)

    async def wrapper() -> AsyncIterator[S]:
        for item in cast(Iterable[S], iterable):
            yield item

    return wrapper()
