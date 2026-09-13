from typing import Any

from fastsprout.core.types import AnyIterable
from fastsprout.data.backend.sql.base import SQLBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Deletable

__all__ = ["SQLDeletable"]


class SQLDeletable[E: SQLEntity[Any], Q: SQLQuery](
    Deletable[E, Q], SQLBackend[E]
):
    async def delete(self, entity: E, /) -> None: ...
    async def bulk_delete(self, entities: AnyIterable[E], /) -> None: ...
    async def delete_by_query(self, query: Q, /) -> int: ...
