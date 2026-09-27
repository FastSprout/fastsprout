import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TYPE_CHECKING, Any, Unpack, cast, overload
from uuid import UUID

from typing_extensions import TypeVarTuple

try:
    from bubus import BaseEvent
    from bubus import EventBus as _BubusEventBus
except ImportError:
    BaseEvent = None
    _BubusEventBus = None

if TYPE_CHECKING:
    from bubus import EventBus as BubusEventBus

from fastsprout.core.action import (
    BaseAction,
    BaseNullableAction,
    BaseSequenceAction,
)
from fastsprout.events.backend.protocols import Brokerable
from fastsprout.events.event import (
    Event,
    Eventable,
    EventState,
    EventStatesGroup,
)

__all__ = ["InMemoryBroker"]

ETs = TypeVarTuple("ETs", default=Unpack[tuple[Eventable, ...]])


class InMemoryBroker(Brokerable):
    """Route events through an in-memory bubus bus."""

    def __init__(self, bus: "BubusEventBus | None" = None) -> None:
        self.__bus = bus
        self.__registered = False
        self.__handlers: list[
            tuple[type[Event], Callable[[Event], Awaitable[object]]]
        ] = []
        self.__states: dict[UUID, EventState[Any]] = {}
        self.__tasks: dict[UUID, list[asyncio.Task[Any]]] = {}
        self.__processing: dict[UUID, asyncio.Task[None]] = {}
        self.__starts: dict[UUID, asyncio.Future[None]] = {}
        self.__started: set[UUID] = set()

    def __native_bus(self) -> "BubusEventBus":
        if not self.__registered:
            if _BubusEventBus is None:
                raise ModuleNotFoundError("Install fastsprout[events] for bubus")
            self.__bus = self.__bus or _BubusEventBus()
            self.__bus.on("FastSproutEnvelope", self.__process)
            self.__registered = True
        assert self.__bus is not None
        return self.__bus

    def subscribe[E: Event](
        self,
        event_type: type[E],
        handler: BaseNullableAction[E, Any]
        | BaseAction[E, Any]
        | BaseSequenceAction[E, Any],
    ) -> None:
        self.__handlers.append(
            (event_type, cast(Callable[[Event], Awaitable[object]], handler))
        )

    async def dispatch[E: Eventable](self, event_state: EventState[E]) -> None:
        event = event_state.event
        event_id = event.__event_id__
        if event_id in self.__states:
            raise ValueError(f"Event already dispatched: {event_id}")

        start: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        tasks: list[asyncio.Task[Any]] = []
        self.__states[event_id] = event_state
        self.__starts[event_id] = start
        self.__tasks[event_id] = tasks

        for event_type, handler in self.__handlers:
            if not isinstance(event, event_type):
                continue

            async def invoke(
                action: Callable[[Event], Awaitable[object]] = handler,
            ) -> object:
                await asyncio.shield(start)
                self.__started.add(event_id)
                return await action(cast(Event, event))

            task = asyncio.create_task(invoke())
            tasks.append(task)
            event_state.result.add_pending(task)

        self.__enqueue(event_id, tasks)

    def __enqueue(self, event_id: UUID, tasks: list[asyncio.Task[Any]]) -> None:
        try:
            if BaseEvent is None:
                raise ModuleNotFoundError("Install fastsprout[events] for bubus")
            envelope = BaseEvent[None](
                event_type="FastSproutEnvelope",
                event_schema="FastSproutEnvelope@1",
                event_id=str(event_id),
            )
            processing = asyncio.create_task(
                self.__native_bus().process_event(envelope)
            )
            self.__processing[event_id] = processing
            processing.add_done_callback(
                lambda _: self.__processing.pop(event_id, None)
            )
        except Exception:
            self.__starts.pop(event_id)
            self.__tasks.pop(event_id)
            del self.__states[event_id]
            for task in tasks:
                task.cancel()
            raise

    async def __process(self, envelope: Any) -> None:
        event_id = UUID(envelope.event_id)
        start = self.__starts.pop(event_id, None)
        if start is None:
            return
        start.set_result(None)
        await asyncio.gather(*self.__tasks[event_id], return_exceptions=True)

    @overload
    async def get[E: Eventable](
        self, event_type: type[E], /
    ) -> AsyncIterator[EventState[E]]: ...

    @overload
    async def get[E: Eventable](self, event: E, /) -> EventState[E] | None: ...

    @overload
    async def get(self, /, *events: *ETs) -> EventStatesGroup[*ETs]: ...

    async def get(self, *items: Any) -> Any:  # noqa: C901
        if len(items) == 1 and isinstance(items[0], type):
            event_type = items[0]

            async def matches() -> AsyncIterator[EventState[Eventable]]:
                for state in tuple(self.__states.values()):
                    if isinstance(state.event, event_type):
                        yield state

            return matches()
        if len(items) == 1:
            return self.__states.get(items[0].__event_id__)

        states = []
        for event in items:
            state = self.__states.get(event.__event_id__)
            if state is None:
                raise LookupError(f"Event is not published: {event!r}")
            states.append(state)
        return EventStatesGroup(*states)

    async def retract[E: Eventable](self, state: EventState[E]) -> bool:
        event_id = state.event.__event_id__
        if self.__states.get(event_id) is not state:
            return False
        if event_id in self.__started:
            return False
        self.__starts.pop(event_id, None)
        processing = self.__processing.pop(event_id, None)
        if processing is not None:
            processing.cancel()
        for task in self.__tasks.pop(event_id, ()):
            task.cancel()
        del self.__states[event_id]
        return True
