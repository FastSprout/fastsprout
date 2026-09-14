from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Any, Protocol, runtime_checkable

from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.types import AnyIterable
from fastsprout.data.capabilities.query import BaseQuery
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
    ) -> AsyncIterator[E]: ...


@runtime_checkable
class UpdatableByQuery[E: Entitieable, Q: BaseQuery](Protocol):
    async def update_by_query(
        self,
        query: Q,
        /,
        *assignments: FieldAssignment[Any],
    ) -> int: ...
