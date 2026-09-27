from collections.abc import AsyncIterator
from typing import Any, Protocol, Unpack, overload, runtime_checkable

from typing_extensions import TypeVarTuple

from fastsprout.core import BaseAction
from fastsprout.core.action import BaseNullableAction, BaseSequenceAction
from fastsprout.events.event import (
    Event,
    Eventable,
    EventState,
    EventStatesGroup,
)

__all__ = ["Brokerable"]
ETs = TypeVarTuple("ETs", default=Unpack[tuple[Eventable, ...]])


@runtime_checkable
class Brokerable(Protocol):
    async def dispatch[E: Eventable](
        self, event_state: EventState[E]
    ) -> None: ...

    def subscribe[E: Event](
        self,
        event_type: type[E],
        handler: BaseNullableAction[E, Any]
        | BaseAction[E, Any]
        | BaseSequenceAction[E, Any],
    ) -> None: ...

    @overload
    async def get[E: Eventable](
        self, event_type: type[E], /
    ) -> AsyncIterator[EventState[E]]: ...
    @overload
    async def get[E: Eventable](self, event: E, /) -> EventState[E] | None: ...
    @overload
    async def get(self, /, *events: *ETs) -> EventStatesGroup[*ETs]: ...

    async def retract[E: Eventable](self, state: EventState[E]) -> bool: ...
