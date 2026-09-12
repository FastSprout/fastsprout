from typing import Any

from fastsprout.core.types import AnyIterable
from fastsprout.data.adapters.sql.base import SQLAdapter
from fastsprout.data.adapters.sql.entity import SQLEntity
from fastsprout.data.adapters.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Deletable

__all__ = ["SQLDeletable"]


class SQLDeletable[E: SQLEntity[Any], Q: SQLQuery](
    Deletable[E, Q], SQLAdapter[E]
):
    async def delete(self, entity: E, /) -> None: ...
    async def bulk_delete(self, entities: AnyIterable[E], /) -> None: ...
    async def delete_by_query(self, query: Q, /) -> int: ...
