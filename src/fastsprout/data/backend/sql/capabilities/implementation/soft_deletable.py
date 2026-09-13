from collections.abc import AsyncIterator, Sequence
from typing import Any

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.entity import SoftDeletableSQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import SoftDeletable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE

__all__ = ["SQLSoftDeletable"]


class SQLSoftDeletable[E: SoftDeletableSQLEntity[Any], Q: SQLQuery](
    SoftDeletable[E, Q]
):
    async def soft_delete(self, entity: E, /) -> None: ...
    async def bulk_soft_delete(self, entities: AnyIterable[E], /) -> None: ...
    async def soft_delete_by_query(self, query: Q, /) -> int: ...

    async def _handle_before_start(
        self,
        entities: AnyIterable[E],
    ) -> AnyIterable[E]:
        return entities

    async def _handle_before_soft_delete(
        self, entities: Sequence[E]
    ) -> Sequence[E]:
        return entities

    async def _handle_after_soft_delete(self, entities: Sequence[E]) -> None:
        return None

    async def _handle_after_complete(self) -> None:
        return None

    async def restore(self, entity: E, /) -> E: ...
    async def bulk_restore(
        self, entities: AnyIterable[E], /
    ) -> Sequence[E]: ...
    async def iter_bulk_restore(
        self,
        entities: AnyIterable[E],
        /,
        *,
        chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE,
    ) -> AsyncIterator[Sequence[E]]: ...

    async def _handle_before_restore(
        self, entities: Sequence[E]
    ) -> Sequence[E]:
        return entities

    async def _handle_after_restore(self, entities: Sequence[E]) -> None:
        return None
