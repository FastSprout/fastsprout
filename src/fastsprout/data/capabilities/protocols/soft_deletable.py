from collections.abc import AsyncGenerator, Sequence
from typing import Any, Protocol, runtime_checkable

from fastsprout.core.types import AnyIterable
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import BaseEntity

__all__ = ["SoftDeletable"]


@runtime_checkable
class SoftDeletable[E: BaseEntity[Any], Q: BaseQuery](Protocol):
    async def soft_delete(self, entity: E, /) -> None: ...
    async def bulk_soft_delete(self, entities: AnyIterable[E], /) -> None: ...
    async def soft_delete_by_query(self, query: Q, /) -> int: ...

    async def _handle_before_start(
        self,
        entities: AnyIterable[E],
    ) -> AnyIterable[E]: ...

    async def _handle_before_soft_delete(
        self, entities: Sequence[E]
    ) -> Sequence[E]: ...

    async def _handle_after_soft_delete(
        self, entities: Sequence[E]
    ) -> None: ...

    async def _handle_after_complete(self) -> None: ...

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
    ) -> AsyncGenerator[Sequence[E], None]: ...

    async def _handle_before_restore(
        self, entities: Sequence[E]
    ) -> Sequence[E]: ...

    async def _handle_after_restore(self, entities: Sequence[E]) -> None: ...
