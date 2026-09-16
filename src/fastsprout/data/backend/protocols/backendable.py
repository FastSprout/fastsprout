from contextlib import AbstractAsyncContextManager
from typing import Protocol, runtime_checkable

from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable, Signpostable

from .finalizable import Finalizable

__all__ = ["Backendable"]


@runtime_checkable
class Backendable[T, F: Finalizable](Protocol):
    def __init__(self, /, signpost: Signpostable[T]) -> None: ...

    def bind(self) -> AbstractAsyncContextManager[F]:
        """Open this backend for the current context; exit releases it."""
        ...

    def query_for[E: Entitieable](self, entity: type[E]) -> BaseQuery:
        """A base (unfiltered) read query in this backend's dialect."""
        ...

    def transaction(self) -> AbstractAsyncContextManager[T]: ...
