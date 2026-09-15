from contextlib import AbstractAsyncContextManager
from typing import Annotated, Any, Protocol, runtime_checkable

from annotated_types import Ge

from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable

__all__ = ["Backendable"]


@runtime_checkable
class Backendable(Protocol):
    priority: Annotated[int, Ge(0)] = 0

    def bind(self) -> AbstractAsyncContextManager[Any]:
        """Open this backend for the current context; exit releases it."""
        ...

    def query_for[E: Entitieable](self, entity: type[E]) -> BaseQuery:
        """A base (unfiltered) read query in this backend's dialect."""
        ...
