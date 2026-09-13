from typing import Any

from fastsprout.data.backend.sql.base import SQLBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Streamable
from fastsprout.data.streams.protocols import AsyncEntityStream

__all__ = ["SQLStreamable"]


class SQLStreamable[E: SQLEntity[Any], Q: SQLQuery](
    Streamable[E, Q], SQLBackend[E]
):
    def stream(self, query: Q, /) -> AsyncEntityStream[E]: ...
