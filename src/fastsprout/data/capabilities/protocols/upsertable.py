from collections.abc import (
    AsyncGenerator,
    Sequence,
)
from typing import Any, Protocol, runtime_checkable

from fastsprout.core.types import AnyIterable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import BaseEntity

__all__ = ["Upsertable"]


@runtime_checkable
class Upsertable[E: BaseEntity[Any]](Protocol):
    async def upsert(self, entity: E, /) -> E: ...
    async def bulk_upsert(self, entities: AnyIterable[E], /) -> Sequence[E]: ...
    async def iter_bulk_upsert(
        self,
        entities: AnyIterable[E],
        /,
        *,
        chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE,
    ) -> AsyncGenerator[Sequence[E], None]: ...
