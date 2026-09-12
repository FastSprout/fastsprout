from collections.abc import (
    AsyncIterable,
    Sequence,
)
from typing import Any, Protocol, runtime_checkable

from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import BaseEntity

__all__ = ["Iterable"]


@runtime_checkable
class Iterable[E: BaseEntity[Any], Q: BaseQuery](Protocol):
    async def iter(self, query: Q, /) -> AsyncIterable[E]: ...
    async def iter_per(
        self, query: Q, /, *, chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE
    ) -> AsyncIterable[Sequence[E]]: ...
