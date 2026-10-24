from uuid import UUID

import pytest

from fastsprout.core import dataclass
from fastsprout.events import Event, EventBus, EventState
from fastsprout.events.backend.in_memory import InMemoryBroker
from fastsprout.events.event import Eventable
from fastsprout.events.middleware import EventsMiddleware, MiddlewareBindable
from fastsprout.testing.core import given, then, when

from ..backend.base_test_broker import Message


class OtherMessage(Event): ...


type AnyEventState = EventState[Eventable]


class ConfiguredRecorder:
    def __init__(
        self, bus: EventBus, /, label: str, *, enabled: bool = True
    ) -> None:
        self.bus = bus
        self.label = label
        self.enabled = enabled

    async def __call__(self, state: EventState[Message]) -> None:
        if self.enabled:
            await state.wait()


@dataclass
class Observation:
    bus: EventBus
    event: Message
    results: tuple[int, ...]


class TestEventsMiddleware:
    @when("a middleware registration is represented with its configuration")
    def representation(self) -> str:
        return repr(
            EventsMiddleware(ConfiguredRecorder, "audit", enabled=False)
        )

    @then("the representation names the factory and all configured arguments")
    def test_representation(self, representation: str) -> None:
        assert representation == (
            "EventsMiddleware(ConfiguredRecorder, 'audit', enabled=False)"
        )

    @given("a recorder of middleware calls")
    def seen(self) -> list[Observation]:
        return []

    @given("middleware registered at construction and through add_middleware")
    def middleware_bus(
        self, broker: InMemoryBroker, seen: list[Observation]
    ) -> EventBus:
        class Recorder:
            def __init__(self, bus: EventBus, /) -> None:
                self.bus = bus

            async def __call__(self, state: EventState[Message]) -> None:
                result = await state.wait()
                done, _ = result
                seen.append(
                    Observation(
                        self.bus,
                        state.event,
                        tuple(item.value for item in done),
                    )
                )

        bus = EventBus(broker, middleware=[EventsMiddleware(Recorder)])
        bus.add_middleware(Recorder)

        async def handler(event: Message) -> Message:
            return Message(value=event.value + 1)

        bus.subscribe(Message, handler)
        return bus

    @when("a matching message and an unrelated message are published")
    async def published(self, middleware_bus: EventBus) -> None:
        await middleware_bus.publish(Message(value=1), OtherMessage())

    @then("only the annotated event reaches both middleware registrations")
    def test_annotated_event(
        self, middleware_bus: EventBus, seen: list[Observation], published: None
    ) -> None:
        assert [call.event.value for call in seen] == [1, 1]
        assert all(call.bus is middleware_bus for call in seen)
        assert all(call.results == (2,) for call in seen)


class TestGeneralMiddleware:
    @given("a recorder of event identities")
    def identities(self) -> list[UUID]:
        return []

    @given("middleware accepting all events through a static call or alias")
    def binding(
        self, identities: list[UUID], static: bool
    ) -> MiddlewareBindable:
        class StaticRecorder:
            def __init__(self, bus: EventBus, /) -> None:
                self.bus = bus

            @staticmethod
            async def __call__(state: EventState[Eventable]) -> None:
                identities.append(state.event.__event_id__)

        class AliasRecorder:
            def __init__(self, bus: EventBus, /) -> None:
                self.bus = bus

            async def __call__(self, state: AnyEventState) -> None:
                identities.append(state.event.__event_id__)

        return (
            EventsMiddleware[Eventable, []](StaticRecorder)
            if static
            else EventsMiddleware[Eventable, []](AliasRecorder)
        )

    @when("two event types pass through the middleware")
    async def published(
        self, broker: InMemoryBroker, binding: MiddlewareBindable
    ) -> list[UUID]:
        bus = EventBus(broker, middleware=[binding])
        events = (Message(value=1), OtherMessage())
        await bus.publish(*events)
        return [event.__event_id__ for event in events]

    @pytest.mark.parametrize("static", [False, True])
    @then("general middleware receives each event exactly once")
    def test_all_events(
        self, identities: list[UUID], published: list[UUID]
    ) -> None:
        assert identities == published
