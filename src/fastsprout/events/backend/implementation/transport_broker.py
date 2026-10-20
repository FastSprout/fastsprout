from abc import ABC, abstractmethod
from asyncio import Lock
from collections.abc import Awaitable, Callable, Iterator
from uuid import UUID

from pydantic import TypeAdapter

from fastsprout.core import BaseSchema
from fastsprout.core.action import (
    BaseAction,
    BaseNullableAction,
    BaseSequenceAction,
)
from fastsprout.core.schema import Schema
from fastsprout.events.event import Event, Eventable, EventState

from .in_memory_broker import InMemoryBroker

__all__ = ["EventMessage", "TransportBroker", "event_route", "event_types"]


class EventMessage(BaseSchema):
    event_id: UUID
    payload: str


def event_route(event_type: type[Eventable]) -> str:
    return f"{event_type.__module__}.{event_type.__qualname__}"


def event_types(event: Eventable) -> Iterator[type[Eventable]]:
    yield type(event)
    if isinstance(event, Event):
        for parent in type(event).__mro__[1:]:
            if issubclass(parent, Event):
                yield parent


class TransportBroker(InMemoryBroker, ABC):
    """Keep EventState semantics while transporting events through a broker."""

    def __init__(self) -> None:
        super().__init__()
        self.registered_events: set[type[Event]] = set()
        self.subscriptions: list[Callable[[], Awaitable[None]]] = []
        self.start_lock = Lock()
        self.connected = False

    def subscribe[E: Event](
        self,
        event_type: type[E],
        handler: BaseAction[E, Schema]
        | BaseNullableAction[E, Schema | None]
        | BaseSequenceAction[E, Schema],
    ) -> None:
        super().subscribe(event_type, handler)
        if event_type in self.registered_events:
            return

        async def receive(message: EventMessage) -> None:
            event = event_type.from_transport(message.payload, message.event_id)
            state = await self.get(event)
            if state is None:
                self.prepare(EventState(event))
            await self.deliver(message.event_id, raise_errors=True)

        self.subscriptions.append(self.register(event_type, receive))
        self.registered_events.add(event_type)

    async def dispatch[E: Eventable](self, event_state: EventState[E]) -> None:
        await self.start()
        self.prepare(event_state)
        await self.publish(event_state)

    async def start(self) -> None:
        async with self.start_lock:
            if not self.connected:
                await self.connect()
                self.connected = True
            while self.subscriptions:
                await self.subscriptions[0]()
                self.subscriptions.pop(0)

    async def publish[E: Eventable](self, state: EventState[E]) -> None:
        try:
            message = EventMessage(
                event_id=state.event.__event_id__,
                payload=TypeAdapter(type(state.event))
                .dump_json(state.event)
                .decode(),
            )
            for event_type in event_types(state.event):
                await self.send(message, event_type)
        except BaseException:
            await super().retract(state)
            raise

    async def retract[E: Eventable](self, state: EventState[E]) -> bool:
        return False

    @abstractmethod
    def register(
        self,
        event_type: type[Event],
        handler: Callable[[EventMessage], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]: ...

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def send(
        self, message: EventMessage, event_type: type[Eventable]
    ) -> None: ...
