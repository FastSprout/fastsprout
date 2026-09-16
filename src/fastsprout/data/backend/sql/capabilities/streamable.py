from typing import Any

from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.backend.sql.streams.entity_stream import SQLEntityStream
from fastsprout.data.capabilities.protocols import Streamable

__all__ = ["SQLStreamable"]


class SQLStreamable[E: SQLEntity[Any], Q: SQLQuery](
    Streamable[E, Q], SQLDataBackend
):
    def stream(self, query: SQLQuery[E], /):
        return SQLEntityStream(query._built_query, self._signpost)
