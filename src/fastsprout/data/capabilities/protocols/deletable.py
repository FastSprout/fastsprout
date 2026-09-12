from typing import Any, Protocol, runtime_checkable

from fastsprout.core.types import AnyIterable
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import BaseEntity

__all__ = ["Deletable"]


@runtime_checkable
class Deletable[E: BaseEntity[Any], Q: BaseQuery](Protocol):
    async def delete(self, entity: E, /) -> None: ...
    async def bulk_delete(self, entities: AnyIterable[E], /) -> None: ...
    async def delete_by_query(self, query: Q, /) -> int: ...
