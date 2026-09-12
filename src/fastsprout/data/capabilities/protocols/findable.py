from collections.abc import (
    Sequence,
)
from typing import Protocol, runtime_checkable

from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable

__all__ = ["Findable"]


@runtime_checkable
class Findable[E: Entitieable, Q: BaseQuery](Protocol):
    async def find_first(self, query: Q, /) -> E | None: ...
    async def find_exactly_one(self, query: Q, /) -> E: ...
    async def find_all(self, query: Q, /) -> Sequence[E]: ...
