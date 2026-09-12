from typing import Any, Protocol, runtime_checkable

from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import BaseEntity
from fastsprout.data.streams.protocols import AsyncEntityStream

__all__ = ["Streamable"]


@runtime_checkable
class Streamable[E: BaseEntity[Any], Q: BaseQuery](Protocol):
    def stream(self, query: Q, /) -> AsyncEntityStream[E]: ...
