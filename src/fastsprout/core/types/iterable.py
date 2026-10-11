from collections.abc import AsyncIterable, AsyncIterator

from .protocols.ables import AIterable, Iterable

__all__ = ["AnyIterable", "Chunk"]

type AnyIterable[S] = Iterable[S] | AIterable[S]


class Chunk[T](AsyncIterable[T]):
    """A lazy input batch that dependencies may replace."""

    def __init__(self, source: AsyncIterable[T]) -> None:
        self.source: AsyncIterable[T] = source

    def __aiter__(self) -> AsyncIterator[T]:
        return aiter(self.source)
