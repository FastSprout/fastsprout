from typing import Any

from fastsprout.data.adapters.sql.base import SQLAdapter
from fastsprout.data.adapters.sql.entity import SQLEntity
from fastsprout.data.adapters.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Streamable
from fastsprout.data.streams.protocols import AsyncEntityStream

__all__ = ["SQLStreamable"]


class SQLStreamable[E: SQLEntity[Any], Q: SQLQuery](
    Streamable[E, Q], SQLAdapter[E]
):
    def stream(self, query: Q, /) -> AsyncEntityStream[E]: ...
