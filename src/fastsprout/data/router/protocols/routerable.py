from types import TracebackType
from typing import Any, Protocol, Self, runtime_checkable

from fastsprout.data.backend.protocols import DataAbilitable, Finalizable
from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.protocols import AsyncEntityStream

__all__ = ["Routerable"]


@runtime_checkable
class Routerable(Finalizable, Protocol):
    def __init__(self) -> None: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def ability[E: Entitieable[Any]](
        self, entity: type[E]
    ) -> DataAbilitable[E, Any, BaseQuery[E, Any], Finalizable]: ...

    def stream[E: Entitieable[Any]](
        self, q: BaseQuery[E, Any]
    ) -> AsyncEntityStream[E]: ...

    async def finalize(self) -> None:
        """Flush staged intents, then finalize bound backends —
        highest `priority` first."""
        ...

    async def abort(self) -> None:
        """Drop staged intents and abort bound backends."""
        ...
