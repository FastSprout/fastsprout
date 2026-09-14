from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Any, Protocol, runtime_checkable

from fastsprout.core.types import AnyIterable
from fastsprout.data.entity import Entitieable

__all__ = ["Creatable"]


@runtime_checkable
class Creatable[E: Entitieable[Any]](Protocol):
    async def create(self, entity: E, /) -> E: ...
    async def bulk_create(self, entities: Sequence[E], /) -> Sequence[E]: ...
    async def iter_bulk_create(
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]: ...
