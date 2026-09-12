from typing import Protocol, runtime_checkable

from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.protocols import AsyncEntityStream

__all__ = ["Streamable"]


@runtime_checkable
class Streamable[E: Entitieable, Q: BaseQuery](Protocol):
    def stream(self, query: Q, /) -> AsyncEntityStream[E]: ...
