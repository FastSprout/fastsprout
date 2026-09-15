from types import TracebackType
from typing import Any, Protocol, Self, runtime_checkable

from fastsprout.data.capabilities.protocols import Abilitable
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable

__all__ = ["Routerable"]


@runtime_checkable
class Routerable(Protocol):
    def __init__(self) -> None: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def _stage[E: Entitieable[Any]](self, entity: E) -> None:  # pyright: ignore[reportInvalidTypeVarUse]
        """Register an intent to persist — pure bookkeeping, no I/O."""
        ...

    def ability[E: Entitieable[Any]](
        self, source: type[E] | BaseQuery[E, Any]
    ) -> Abilitable[E, BaseQuery[E, Any]]: ...  # pyright: ignore[reportInvalidTypeArguments]

    async def finalize(self) -> None:
        """Flush staged intents, then finalize bound backends —
        highest `priority` first."""
        ...

    async def abort(self) -> None:
        """Drop staged intents and abort bound backends."""
        ...
