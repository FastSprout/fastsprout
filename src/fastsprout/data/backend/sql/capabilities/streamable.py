from typing import Any

from sqlalchemy.sql import Select

from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.streams.entity_stream import SQLEntityStream
from fastsprout.data.capabilities.protocols import Streamable
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.streams.protocols import AsyncEntityStream

__all__ = ["SQLStreamable"]


class SQLStreamable[E: SQLEntity[Any]](
    Streamable[E, BaseQuery[E, Select[tuple[E]]]], SQLDataBackend
):
    def stream(
        self, query: BaseQuery[E, Select[tuple[E]]], /
    ) -> AsyncEntityStream[E]:
        return SQLEntityStream(query, self._signpost)
