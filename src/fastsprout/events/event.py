import asyncio
from collections.abc import Iterator, Sequence
from datetime import timedelta
from typing import (
    Any,
    ClassVar,
    Generic,
    Protocol,
    Self,
    Unpack,
    overload,
    runtime_checkable,
)
from uuid import UUID, uuid4

from pydantic import ConfigDict, PrivateAttr
from typing_extensions import TypeVar, TypeVarTuple

from fastsprout.core.schema import BaseSchema, Schema
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
    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True
    )
    # Pydantic requires private attribute names to start with an underscore.
    _event_id: UUID = PrivateAttr(default_factory=uuid4)  # pylint: disable=private-name

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
        self.event_states = event_states

    def __iter__(self) -> Iterator["EventState[Eventable]"]:
        return iter(self.event_states)

    def __repr__(self) -> str:
        states = ", ".join(repr(state) for state in self.event_states)
        return f"{type(self).__name__}({states})"


class EventState[E: Eventable]:
    def __init__(self, /, event: E) -> None:
        self.event_value = event
        self.event_result: EventResult[E] = EventResult(self)

    @property
    def event(self) -> E:
        return self.event_value

    @property
    def result(self) -> "EventResult[E]":
        return self.event_result

    def __repr__(self) -> str:
        return f"{type(self).__name__}(event={self.event_value!r})"

    @overload
    async def wait[R: Schema](
        self,
        schema: type[R],
        *,
        return_when: ReturnWhenLiteral = ALL_COMPLETED,
        timeout: float | None = None,
    ) -> "EventResult[E, R]": ...

    @overload
    async def wait(
        self,
        schema: None = None,
        *,
        return_when: ReturnWhenLiteral = ALL_COMPLETED,
        timeout: float | None = None,
    ) -> "EventResult[E]": ...

    async def wait(
        self,
        schema: type[Schema] | None = None,
        *,
        return_when: ReturnWhenLiteral = ALL_COMPLETED,
        timeout: float | None = None,
    ) -> "EventResult[E]":
        result = (
            self.event_result
            if schema is None
            else self.event_result.route(schema)
        )
        return await result.wait(return_when=return_when, timeout=timeout)


E = TypeVar("E", bound=Eventable)
R = TypeVar("R", bound=Schema, default=Any)


class EventResult(tuple[list[R], list[asyncio.Future[Any]]], Generic[E, R]):
    state: EventState[E]

    def __new__(
        cls, event_state: EventState[E], schema: type[R] | None = None
    ) -> Self:
        successful: list[R] = []
        pending: list[asyncio.Future[Any]] = []
        return tuple.__new__(cls, (successful, pending))

    def __init__(
        self, event_state: EventState[E], schema: type[R] | None = None
    ) -> None:
        self.state = event_state
        self.schema: type[R] | None = schema
        self.success_events: list[R] = self[0]
        self.pending_events: list[asyncio.Future[Any]] = self[1]
        self.error_events: list[BaseException] = []
        self.completion_count: int = 0
        self.seen_completions: int = 0
        self.seen_errors: int = 0
        self.views: dict[type[Schema], EventResult[E, Any]] = {}

    def __eq__(self, other: object) -> bool:
        return self is other

    def __ne__(self, other: object) -> bool:
        return self is not other

    def __hash__(self) -> int:
        return object.__hash__(self)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(state={self.state!r}, "
            f"values={self.success_events!r}, "
            f"pending={len(self.pending_events)}, "
            f"errors={self.error_events!r})"
        )

    @property
    def errors(self) -> tuple[BaseException, ...]:
        return tuple(self.error_events)

    def add_pending(self, future: asyncio.Future[Any]) -> None:
        self.pending_events.append(future)
        future.add_done_callback(self.complete)
        for view in self.views.values():
            view.add_pending(future)

    def route[S: Schema](self, schema: type[S]) -> "EventResult[E, S]":
        if self.schema is not None:
            return self.state.result.route(schema)
        if schema not in self.views:
            view = EventResult(self.state, schema)
            for value in self.success_events:
                view.success_events.extend(view.select(value))
            view.error_events.extend(self.error_events)
            view.completion_count = len(view.success_events) + len(
                view.error_events
            )
            for future in self.pending_events:
                view.add_pending(future)
            self.views[schema] = view
        return self.views[schema]

    def select(self, value: Any) -> list[R]:
        if self.schema is None:
            return [] if value is None else [value]
        if isinstance(value, self.schema):
            return [value]
        if isinstance(value, Sequence):
            return [item for item in value if isinstance(item, self.schema)]
        return []

    def complete(self, future: asyncio.Future[Any]) -> None:
        if future not in self.pending_events:
            return
        self.pending_events.remove(future)
        try:
            value = future.result()
        except BaseException as error:
            self.error_events.append(error)
            self.completion_count += 1
        else:
            selected = self.select(value)
            self.success_events.extend(selected)
            if self.schema is None or selected:
                self.completion_count += 1

    async def wait(
        self,
        *,
        return_when: ReturnWhenLiteral = ALL_COMPLETED,
        timeout: float | None = None,
    ) -> Self:
        deadline = (
            None
            if timeout is None
            else asyncio.get_running_loop().time() + timeout
        )
        seen_completions, seen_errors = self.seen_completions, self.seen_errors
        while self.pending_events and not self.completed(
            return_when, seen_completions, seen_errors
        ):
            remaining = (
                None
                if deadline is None
                else max(0, deadline - asyncio.get_running_loop().time())
            )
            done, _ = await asyncio.wait(
                self.pending_events[:],
                timeout=remaining,
                return_when=return_when,
            )
            for future in done:
                self.complete(future)
            if not done or return_when == ALL_COMPLETED:
                break
        self.seen_completions = self.completion_count
        self.seen_errors = len(self.error_events)
        return self

    def completed(
        self,
        return_when: ReturnWhenLiteral,
        seen_completions: int,
        seen_errors: int,
    ) -> bool:
        return (
            return_when == FIRST_COMPLETED
            and self.completion_count > seen_completions
        ) or (
            return_when == FIRST_EXCEPTION
            and len(self.error_events) > seen_errors
        )

    def __iter__(self) -> Iterator[list[Any]]:
        return iter((self.success_events[:], self.pending_events[:]))
