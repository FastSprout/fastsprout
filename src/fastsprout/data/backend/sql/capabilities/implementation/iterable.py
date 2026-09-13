from collections.abc import (
    AsyncIterable,
    Sequence,
)
from typing import Any

from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Iterable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE

__all__ = ["SQLIterable"]


class SQLIterable[E: SQLEntity[Any], Q: SQLQuery](Iterable[E, Q]):
    async def iter(self, query: Q, /) -> AsyncIterable[E]: ...
    async def iter_per(
        self, query: Q, /, *, chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE
    ) -> AsyncIterable[Sequence[E]]: ...
