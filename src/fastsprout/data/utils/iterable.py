from collections.abc import AsyncIterator

from fastsprout.core.types import AnyIterable
from fastsprout.core.types.iterable import resolve_any_iterable

__all__ = ["achain", "resolve_any_iterable"]


async def achain[T](*its: AnyIterable[T]) -> AsyncIterator[T]:
    for it in its:
        async for item in resolve_any_iterable(it):
            yield item
