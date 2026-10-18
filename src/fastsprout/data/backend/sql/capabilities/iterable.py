from collections.abc import AsyncIterator, Sequence
from typing import Any

from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.backend.sql.streams import SQLEntityStream
from fastsprout.data.capabilities.protocols import Iterable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE

__all__ = ["SQLIterable"]


class SQLIterable[E: SQLEntity[Any]](Iterable[E, SQLQuery[E]], SQLDataBackend):
    def iter(self, query: SQLQuery[E], /) -> AsyncIterator[E]:
        return aiter(SQLEntityStream(query, self._signpost))

    def iter_per(
        self,
        query: SQLQuery[E],
        /,
        *,
        chunk_size: int = DEFAULT_ITERATION_CHUNK_SIZE,
    ) -> AsyncIterator[Sequence[E]]:
        return SQLEntityStream(query, self._signpost).chunked(chunk_size)
