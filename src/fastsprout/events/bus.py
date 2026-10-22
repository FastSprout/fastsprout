import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from functools import cache, partial
from typing import Any, Final, Self, Unpack, cast, overload

from typing_extensions import TypeVarTuple

try:
    from croniter import croniter  # type: ignore[import-untyped]
except ImportError:
    croniter = None

from fastsprout.core.action import (
    Actionable,
    NullableActionable,
    SequenceActionable,
)
from fastsprout.core.depends import inject_depends
from fastsprout.events.backend.implementation import InMemoryBroker
from fastsprout.events.backend.protocols import Brokerable
from fastsprout.events.event import (
    Event,
    Eventable,
    EventState,
    EventStatesGroup,
)
from fastsprout.events.middleware import (
    EventsMiddleware,
    EventsMiddlewareFactoryable,
    MiddlewareBindable,
)

__all__ = ["IN_MEMORY_EVENT_BUS", "EventBus"]

ETs = TypeVarTuple("ETs", default=Unpack[tuple[Eventable, ...]])


class EventGroupInBus[*ETs]:
    def __init__(self, bus: "EventBus", events: tuple[*ETs]) -> None:
        self.bus = bus
        self.events = events
        self.states: EventStatesGroup[*ETs] | None = None

    async def __aenter__(self) -> Self:
        states = [
            await self.bus.publish(cast(Eventable, event))
            for event in self.events
        ]
        self.states = cast(EventStatesGroup[*ETs], EventStatesGroup(*states))
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    @overload
    async def get[E: Eventable](
        self, event_type: type[E], /
    ) -> AsyncIterator[EventState[E]]: ...
    @overload
    async def get[E: Eventable](self, event: E, /) -> EventState[E] | None: ...
    @overload
    async def get(self, /, *events: *ETs) -> EventStatesGroup[*ETs]: ...

    async def get(self, *items: Any) -> Any:
        return await self.bus.get(*items)

    async def as_completed(self) -> AsyncIterator[EventState[Any]]:
        if self.states is None:
            raise RuntimeError("Event group is not entered")
        group = cast(EventStatesGroup[*tuple[Eventable, ...]], self.states)
        async for state in self.bus.as_completed(group):
            yield state


class EventBus:
    def __init__(
        self,
        *brokers: Brokerable,
        middleware: Sequence[MiddlewareBindable] | None = None,
    ):
        self.brokers: tuple[Brokerable, ...]
        if len(brokers) == 0:
            self.brokers = (InMemoryBroker(),)
        else:
            self.brokers = brokers

        self.middleware: list[
            Callable[[EventState[Eventable]], Awaitable[None]]
        ] = [item.resolve(self) for item in middleware or ()]
        self.schedules: list[Callable[[], Awaitable[None]]] = []

    @overload
    async def get[E: Eventable](
        self, event_type: type[E], /
    ) -> AsyncIterator[EventState[E]]: ...

    @overload
    async def get[E: Eventable](self, event: E, /) -> EventState[E] | None: ...
    @overload
    async def get(self, /, *events: *ETs) -> EventStatesGroup[*ETs]: ...

    async def get(self, *items: Any) -> Any:
        return await self.brokers[0].get(*items)

    def subscribe[E: Event](
        self,
        event_type: type[E],
        handler: NullableActionable[E, Any]
        | Actionable[E, Any]
        | SequenceActionable[E, Any],
    ) -> None:
        for broker in self.brokers:
            broker.subscribe(event_type, handler)

    async def retract[E: Eventable](self, state: EventState[E]) -> bool:
        results = [await broker.retract(state) for broker in self.brokers]
        return all(results)

    @overload
    async def publish[E: Eventable](self, event: E) -> EventState[E]: ...
    @overload
    async def publish(self, *events: *ETs) -> EventStatesGroup[*ETs]: ...

    async def publish(self, *events: *ETs) -> EventStatesGroup | EventState:
        if not events:
            raise RuntimeError("Not provided events to publish")
        event_states: list[EventState[Eventable]] = []
        for event in events:
            event_state = EventState(cast(Eventable, event))
            event_states.append(event_state)
            for broker in self.brokers:
                await broker.dispatch(event_state)
        for state in event_states:
            await self.run_middleware(state)
        return (
            EventStatesGroup(*event_states)
            if len(event_states) > 1
            else event_states[0]
        )

    async def run_middleware(self, state: EventState[Eventable]) -> None:
        for handler in self.middleware:
            await handler(state)

    async def as_completed[E: Eventable](
        self,
        event_states_group: EventStatesGroup[*tuple[E, ...]],
    ) -> AsyncIterator[EventState[E]]:
        async def finished(state: EventState[E]) -> EventState[E]:
            await state.wait()
            return state

        completions = [
            finished(cast(EventState[E], state)) for state in event_states_group
        ]
        for completion in asyncio.as_completed(completions):
            yield await completion

    def __call__(self, *events: *ETs) -> EventGroupInBus[*ETs]:
        return EventGroupInBus(self, events)

    def schedule[Result](
        self, on: str | timedelta, action: Callable[[], Awaitable[Result]]
    ) -> None:
        if isinstance(on, timedelta):
            if on.total_seconds() <= 0:
                raise ValueError("Schedule interval must be positive")
        else:
            if croniter is None:
                raise ModuleNotFoundError("Install fastsprout[events] for cron")
            if not croniter.is_valid(on):
                raise ValueError(f"Invalid cron expression: {on!r}")

        self.schedules.append(partial(self.run_schedule, on, action))

    @staticmethod
    async def run_schedule[Result](
        on: str | timedelta, action: Callable[[], Awaitable[Result]]
    ) -> None:
        while True:
            if isinstance(on, timedelta):
                delay = on.total_seconds()
            else:
                if croniter is None:
                    raise ModuleNotFoundError(
                        "Install fastsprout[events] for cron"
                    )
                now = datetime.now(UTC)
                delay = (
                    croniter(on, now).get_next(datetime) - now
                ).total_seconds()
            await asyncio.sleep(max(0, delay))
            await action()

    @asynccontextmanager
    async def scheduler(self) -> AsyncIterator[None]:
        tasks = [asyncio.ensure_future(action()) for action in self.schedules]
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    raise result

    def add_middleware[E: Eventable, **P](
        self,
        middleware: type[EventsMiddlewareFactoryable[E, P]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        item = EventsMiddleware(middleware, *args, **kwargs)
        self.middleware.append(item.resolve(self))


@cache
def get_default_event_bus() -> EventBus:
    return EventBus()


IN_MEMORY_EVENT_BUS: Final[EventBus] = get_default_event_bus()
inject_depends.dependency_providers[EventBus] = get_default_event_bus
