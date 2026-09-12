from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Any, Protocol, runtime_checkable

from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.types import AnyIterable
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import Entitieable

__all__ = ["Updatable", "UpdatableByQuery"]


@runtime_checkable
class Updatable[E: Entitieable](Protocol):
    async def update(self, entity: E, /) -> E: ...
    async def bulk_update(self, entities: AnyIterable[E], /) -> Sequence[E]: ...
    async def iter_bulk_update(
        self,
        entities: AnyIterable[E],
        /,
        *,
        chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE,
    ) -> AsyncIterator[Sequence[E]]: ...

    async def _handle_before_start(
        self,
        entities: AnyIterable[E],
    ) -> AnyIterable[E]: ...

    async def _handle_before_update(
        self, entities: Sequence[E]
    ) -> Sequence[E]: ...

    async def _handle_after_update(self, entities: Sequence[E]) -> None: ...

    async def _handle_after_complete(self) -> None: ...


@runtime_checkable
class UpdatableByQuery[E: Entitieable, Q: BaseQuery](Protocol):
    async def update_by_query(
        self,
        query: Q,
        /,
        *assignments: FieldAssignment[Any],
    ) -> int: ...

    async def _handle_before_start(
        self,
        entities: AnyIterable[E],
    ) -> AnyIterable[E]: ...

    async def _handle_before_update_by_query(
        self, entities: Sequence[E]
    ) -> Sequence[E]: ...

    async def _handle_after_update(self, entities: Sequence[E]) -> None: ...

    async def _handle_after_complete(self) -> None: ...
