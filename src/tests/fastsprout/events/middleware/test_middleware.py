from fastsprout.core import dataclass
from fastsprout.events import Event, EventBus, EventState
from fastsprout.events.backend.in_memory import InMemoryBroker
from fastsprout.events.middleware import EventsMiddleware
from fastsprout.testing.core import given, then, when

from ..backend.base_test_broker import Message


class OtherMessage(Event): ...


@dataclass
class Observation:
    bus: EventBus
    event: Message
    results: tuple[int, ...]


class TestEventsMiddleware:
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
