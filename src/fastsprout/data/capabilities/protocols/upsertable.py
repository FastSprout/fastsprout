from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Protocol, runtime_checkable

from fastsprout.core.types import AnyIterable
from fastsprout.data.entity import Entitieable

__all__ = ["Upsertable"]


@runtime_checkable
class Upsertable[E: Entitieable](Protocol):
    async def upsert(self, entity: E, /) -> E: ...
    async def bulk_upsert(self, entities: AnyIterable[E], /) -> Sequence[E]: ...
    async def iter_bulk_upsert(
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]: ...
