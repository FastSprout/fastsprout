from collections.abc import (
    Sequence,
)
from typing import Any, Protocol, runtime_checkable

from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import BaseEntity

__all__ = ["Findable"]


@runtime_checkable
class Findable[E: BaseEntity[Any], Q: BaseQuery](Protocol):
    async def find_first(self, query: Q, /) -> E | None: ...
    async def find_exactly_one(self, query: Q, /) -> E: ...
    async def find_all(self, query: Q, /) -> Sequence[E]: ...
