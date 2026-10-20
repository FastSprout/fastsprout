import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TYPE_CHECKING, Any, Unpack, cast, overload
from uuid import UUID

from typing_extensions import TypeVarTuple

try:
    from bubus import BaseEvent
    from bubus import EventBus as NativeBubusEventBus
except ImportError:
    BaseEvent = None
    NativeBubusEventBus = None

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
        self.bus = bus
        self.registered = False
        self.handlers: list[
            tuple[type[Event], Callable[[Event], Awaitable[object]]]
        ] = []
        self.states: dict[UUID, EventState[Any]] = {}
        self.tasks: dict[UUID, list[asyncio.Task[Any]]] = {}
        self.processing: dict[UUID, asyncio.Task[None]] = {}
        self.starts: dict[UUID, asyncio.Future[None]] = {}
        self.started: set[UUID] = set()

    def native_bus(self) -> "BubusEventBus":
        if not self.registered:
            if NativeBubusEventBus is None:
                raise ModuleNotFoundError(
                    "Install fastsprout[events] for bubus"
                )
            self.bus = self.bus or NativeBubusEventBus()
            self.bus.on("FastSproutEnvelope", self.process)
            self.registered = True
        assert self.bus is not None
        return self.bus

    def subscribe[E: Event](
        self,
        event_type: type[E],
        handler: BaseNullableAction[E, Any]
        | BaseAction[E, Any]
        | BaseSequenceAction[E, Any],
    ) -> None:
        self.handlers.append(
            (event_type, cast(Callable[[Event], Awaitable[object]], handler))
        )

    async def dispatch[E: Eventable](self, event_state: EventState[E]) -> None:
        self.prepare(event_state)
        self.enqueue(event_state)

    def prepare[E: Eventable](self, event_state: EventState[E]) -> None:
        event = event_state.event
        event_id = event.__event_id__
        if event_id in self.states:
            raise ValueError(f"Event already dispatched: {event_id}")

        start: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        tasks: list[asyncio.Task[Any]] = []
        self.states[event_id] = event_state
        self.starts[event_id] = start
        self.tasks[event_id] = tasks

        for event_type, handler in self.handlers:
            if not isinstance(event, event_type):
                continue

            async def invoke(
                action: Callable[[Event], Awaitable[object]] = handler,
            ) -> object:
                await asyncio.shield(start)
                self.started.add(event_id)
                return await action(cast(Event, event))

            task = asyncio.create_task(invoke())
            tasks.append(task)
            event_state.result.add_pending(task)

    def enqueue[E: Eventable](self, state: EventState[E]) -> None:
        event_id = state.event.__event_id__
        tasks = self.tasks[event_id]
        try:
            if BaseEvent is None:
                raise ModuleNotFoundError(
                    "Install fastsprout[events] for bubus"
                )
            envelope = BaseEvent[None](
                event_type="FastSproutEnvelope",
                event_schema="FastSproutEnvelope@1",
                event_id=str(event_id),
            )
            processing = asyncio.create_task(
                self.native_bus().process_event(envelope)
            )
            self.processing[event_id] = processing
            processing.add_done_callback(
                lambda _: self.processing.pop(event_id, None)
            )
        except Exception:
            self.starts.pop(event_id)
            self.tasks.pop(event_id)
            del self.states[event_id]
            for task in tasks:
                task.cancel()
            raise

    async def process(self, envelope: Any) -> None:
        await self.deliver(UUID(envelope.event_id))

    async def deliver(
        self, event_id: UUID, *, raise_errors: bool = False
    ) -> None:
        start = self.starts.pop(event_id, None)
        if start is None:
            return
        start.set_result(None)
        results = await asyncio.gather(
            *self.tasks[event_id], return_exceptions=True
        )
        if raise_errors:
            for result in results:
                if isinstance(result, BaseException):
                    raise result

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
                for state in tuple(self.states.values()):
                    if isinstance(state.event, event_type):
                        yield state

            return matches()
        if len(items) == 1:
            return self.states.get(items[0].__event_id__)

        states = []
        for event in items:
            state = self.states.get(event.__event_id__)
            if state is None:
                raise LookupError(f"Event is not published: {event!r}")
            states.append(state)
        return EventStatesGroup(*states)

    async def retract[E: Eventable](self, state: EventState[E]) -> bool:
        event_id = state.event.__event_id__
        if self.states.get(event_id) is not state:
            return False
        if event_id in self.started:
            return False
        self.starts.pop(event_id, None)
        processing = self.processing.pop(event_id, None)
        if processing is not None:
            processing.cancel()
        for task in self.tasks.pop(event_id, ()):
            task.cancel()
        del self.states[event_id]
        return True

    async def stop(self) -> None:
        tasks = [task for batch in self.tasks.values() for task in batch]
        tasks.extend(self.processing.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.starts.clear()
        self.tasks.clear()
        self.processing.clear()
