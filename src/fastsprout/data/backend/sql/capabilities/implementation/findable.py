from collections.abc import (
    Sequence,
)
from typing import Any

from fastsprout.data.backend.sql.base import SQLBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Findable

__all__ = ["SQLFindable"]


class SQLFindable[E: SQLEntity[Any], Q: SQLQuery](
    Findable[E, Q], SQLBackend[E]
):
    async def find_first(self, query: Q, /) -> E | None: ...
    async def find_exactly_one(self, query: Q, /) -> E: ...
    async def find_all(self, query: Q, /) -> Sequence[E]: ...
