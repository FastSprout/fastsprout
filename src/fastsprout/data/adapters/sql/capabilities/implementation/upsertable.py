from collections.abc import (
    AsyncIterator,
    Sequence,
)
from typing import Any

from fastsprout.core.types import AnyIterable
from fastsprout.data.adapters.sql.base import SQLAdapter
from fastsprout.data.adapters.sql.entity import SQLEntity
from fastsprout.data.capabilities.protocols import Updatable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE

__all__ = ["SQLUpsertable"]


class SQLUpsertable[E: SQLEntity[Any]](Updatable[E], SQLAdapter[E]):
    async def upsert(self, entity: E, /) -> E: ...
    async def bulk_upsert(self, entities: AnyIterable[E], /) -> Sequence[E]: ...
    async def iter_bulk_upsert(
        self,
        entities: AnyIterable[E],
        /,
        *,
        chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE,
    ) -> AsyncIterator[Sequence[E]]: ...
