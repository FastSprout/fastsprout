from collections.abc import AsyncIterator, Sequence
from typing import Protocol, runtime_checkable

from fastsprout.core.types import AnyIterable
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable

__all__ = ["SoftDeletable"]


@runtime_checkable
class SoftDeletable[E: Entitieable, Q: BaseQuery](Protocol):
    async def soft_delete(self, entity: E, /) -> None: ...
    async def bulk_soft_delete(self, entities: AnyIterable[E], /) -> None: ...
    async def soft_delete_by_query(self, query: Q, /) -> int: ...

    async def restore(self, entity: E, /) -> E: ...
    async def bulk_restore(
        self, entities: AnyIterable[E], /
    ) -> Sequence[E]: ...
    async def iter_bulk_restore(
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]: ...
