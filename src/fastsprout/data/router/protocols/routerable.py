from abc import abstractmethod
from collections.abc import Sequence
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    Self,
    overload,
    runtime_checkable,
)

from fastsprout.core.depends import DependsClass
from fastsprout.data.backend.protocols import DataAbilitable, Finalizable
from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.capabilities.query import JoinedQueryable
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.protocols import (
    AsyncEntityStreamable,
    AsyncJoinedStreamable,
)
from fastsprout.events import EventBus

if TYPE_CHECKING:
    from fastsprout.data.router.implementation.routed_join import RoutedJoin

__all__ = ["Routerable"]


@runtime_checkable
class Routerable(Finalizable, Protocol):
    def __init__(
        self,
        *,
        bus: EventBus | None = None,
        dependencies: Sequence[DependsClass] = (),
    ) -> None: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def ability[E: Entitieable](
        self, entity: type[E]
    ) -> DataAbilitable[E, Any, BaseQuery[E, Any], Finalizable]: ...

    @overload
    def stream[E: Entitieable, ContextT, *Ts](
        self, q: JoinedQueryable[E, ContextT, *Ts]
    ) -> AsyncJoinedStreamable[*Ts]: ...

    @overload
    def stream[E: Entitieable, StatementT](
        self, q: BaseQuery[E, StatementT]
    ) -> AsyncEntityStreamable[E]: ...

    def join[E: Entitieable, StatementT](
        self, q: BaseQuery[E, StatementT]
    ) -> "RoutedJoin[E]": ...

    @abstractmethod
    async def finalize(self) -> None:
        """Flush staged intents, then finalize bound backends —
        highest `priority` first."""

    @abstractmethod
    async def abort(self) -> None:
        """Drop staged intents and abort bound backends."""
