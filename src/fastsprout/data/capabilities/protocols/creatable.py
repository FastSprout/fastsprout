from collections.abc import (
    AsyncGenerator,
    Sequence,
)
from typing import Any, Protocol, runtime_checkable

from fastsprout.core.types import AnyIterable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import BaseEntity

__all__ = ["Creatable"]


@runtime_checkable
class Creatable[E: BaseEntity[Any]](Protocol):
    async def create(self, entity: E, /) -> E: ...
    async def bulk_create(self, entities: Sequence[E], /) -> Sequence[E]: ...
    async def iter_bulk_create(
        self,
        entities: AnyIterable[E],
        /,
        *,
        chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE,
    ) -> AsyncGenerator[Sequence[E], None]: ...

    async def _handle_before_start(
        self,
        entities: AnyIterable[E],
    ) -> AnyIterable[E]: ...

    async def _handle_before_add(
        self, entities: Sequence[E]
    ) -> Sequence[E]: ...

    async def _handle_after_add(self, entities: Sequence[E]) -> None: ...

    async def _handle_after_complete(self) -> None: ...
