from typing import Any

from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity, SQLSource
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.backend.sql.streams.entity_stream import SQLEntityStream
from fastsprout.data.capabilities.protocols import Streamable
from fastsprout.data.streams.protocols import AsyncEntityStream

__all__ = ["SQLStreamable"]


class SQLStreamable[E: SQLEntity[Any]](
    Streamable[E, SQLQuery[E]], SQLDataBackend
):
    def stream[S: SQLSource](
        self, query: SQLQuery[E, S], /
    ) -> AsyncEntityStream[E]:
        return SQLEntityStream(query, self._signpost)
