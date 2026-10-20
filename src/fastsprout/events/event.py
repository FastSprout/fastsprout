import asyncio
from datetime import timedelta
from typing import Any, ClassVar, Protocol, Self, Unpack, runtime_checkable
from uuid import UUID, uuid4

from pydantic import ConfigDict, PrivateAttr
from typing_extensions import TypeVarTuple

from fastsprout.core.schema import BaseSchema
from fastsprout.events.consts import (
    ALL_COMPLETED,
    FIRST_COMPLETED,
    FIRST_EXCEPTION,
)
from fastsprout.events.types import ReturnWhenLiteral

__all__ = [
    "Event",
    "EventResult",
    "EventState",
    "EventStatesGroup",
    "Eventable",
    "ScheduleEvent",
]


@runtime_checkable
class Eventable(Protocol):
    @property
    def __event_id__(self) -> UUID: ...


class Event(BaseSchema):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _event_id: UUID = PrivateAttr(default_factory=uuid4)

    @property
    def __event_id__(self) -> UUID:
        return self._event_id

    @classmethod
    def from_transport(cls, payload: str, event_id: UUID) -> Self:
        """Restore the sender's identity when decoding a transported event."""
        event = cls.model_validate_json(payload)
        event.__pydantic_private__ = dict(
            event.__pydantic_private__ or {}, _event_id=event_id
        )
        return event


class ScheduleEvent(Event):
    __when__: ClassVar[timedelta]


ETs = TypeVarTuple("ETs", default=Unpack[tuple[Eventable, ...]])


class EventStatesGroup[*ETs]:
    def __init__(self, *event_states: "EventState[Eventable]") -> None:
        self.__event_states = event_states

    def __iter__(self):
        return iter(self.__event_states)

    def __repr__(self) -> str:
        states = ", ".join(repr(state) for state in self.__event_states)
        return f"{type(self).__name__}({states})"


class EventState[E: Eventable]:
    def __init__(self, /, event: E) -> None:
        self.__event = event
        self.__result = EventResult(self)
        self.__seen_completions = 0
        self.__seen_errors = 0

    @property
    def event(self) -> E:
        return self.__event

    @property
    def result(self) -> "EventResult[E]":
        return self.__result

    def __repr__(self) -> str:
        return f"{type(self).__name__}(event={self.__event!r})"

    async def wait(
        self,
        *,
        return_when: ReturnWhenLiteral = ALL_COMPLETED,
        timeout: int | None = None,
    ) -> "EventResult[E]":
        pending = self.__result._pedding_events[:]
        already_completed = (
            return_when == FIRST_COMPLETED
            and self.__result._completion_count > self.__seen_completions
        ) or (
            return_when == FIRST_EXCEPTION
            and len(self.__result._error_events) > self.__seen_errors
        )
        if pending and not already_completed:
            done, _ = await asyncio.wait(
                pending, timeout=timeout, return_when=return_when
            )
            for future in done:
                self.__result._complete(future)
        self.__seen_completions = self.__result._completion_count
        self.__seen_errors = len(self.__result._error_events)
        return self.__result


class EventResult[E: Eventable]:
    def __init__(self, event_state: EventState[E]):
        self.state = event_state
        self._success_events: list[Any] = []
        self._pedding_events: list[Any] = []
        self._error_events: list[BaseException] = []
        self._completion_count = 0

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(state={self.state!r}, "
            f"values={self._success_events!r}, "
            f"pending={len(self._pedding_events)}, "
            f"errors={self._error_events!r})"
        )

    @property
    def errors(self) -> tuple[BaseException, ...]:
        return tuple(self._error_events)

    def add_pending(self, future: asyncio.Future[Any]) -> None:
        self._pedding_events.append(future)
        future.add_done_callback(self._complete)

    def _complete(self, future: asyncio.Future[Any]) -> None:
        if future not in self._pedding_events:
            return
        self._pedding_events.remove(future)
        self._completion_count += 1
        try:
            value = future.result()
        except BaseException as error:
            self._error_events.append(error)
        else:
            if value is not None:
                self._success_events.append(value)

    def __iter__(
        self,
    ):
        return iter((self._success_events[:], self._pedding_events[:]))
