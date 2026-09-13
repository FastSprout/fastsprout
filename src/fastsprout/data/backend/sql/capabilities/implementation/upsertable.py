from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Any

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.base import SQLBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.capabilities.protocols import Updatable

__all__ = ["SQLUpsertable"]


class SQLUpsertable[E: SQLEntity[Any]](Updatable[E], SQLBackend[E]):
    async def upsert(self, entity: E, /) -> E: ...
    async def bulk_upsert(self, entities: AnyIterable[E], /) -> Sequence[E]: ...
    async def iter_bulk_upsert(
        self,
        entities: AnyIterable[E],
        /,
    ) -> AsyncIterator[E]: ...
