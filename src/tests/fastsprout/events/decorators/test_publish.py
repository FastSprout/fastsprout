import asyncio
from datetime import timedelta

import pytest

from fastsprout.core import Depends, inject_depends
from fastsprout.events import EventBus, EventState, pub, sub
from fastsprout.events.bus import IN_MEMORY_EVENT_BUS
from fastsprout.testing.core import given, then, when

from ..backend.base_test_broker import Message


class TestPublisher:
    @when("the default EventBus dependency is resolved")
    def resolved(self) -> EventBus:
        bus: EventBus = Depends()
        return inject_depends.resolve(bus, EventBus)

    @then("Depends resolves the shared default bus")
    def test_default_bus(self, resolved: EventBus) -> None:
        assert resolved is IN_MEMORY_EVENT_BUS

    @when("a decorated publisher returns a message")
    async def published(self, bus: EventBus) -> Message:
        @pub(bus=bus)
        async def produce() -> Message:
            return Message(value=1)

        return await produce()

    @then("the publisher preserves the return value and registers its state")
    async def test_return_value(
        self, bus: EventBus, published: Message
    ) -> None:
        state = await bus.get(published)
        assert state is not None
        assert state.event is published

    @given("the default EventBus provider is overridden for this scenario")
    def overridden_bus(
        self, bus: EventBus, monkeypatch: pytest.MonkeyPatch
    ) -> EventBus:
        monkeypatch.setitem(
            inject_depends.dependency_overrides, EventBus, lambda: bus
        )
        return bus

    @when("publisher and subscriber decorators resolve the overridden bus")
    async def overridden_publication(
        self, overridden_bus: EventBus
    ) -> tuple[Message, EventState[Message] | None]:
        @pub()
        async def produce() -> Message:
            return Message(value=1)

        @sub(Message)
        async def handler(event: Message) -> Message:
            return Message(value=event.value + 1)

        event = await produce()
        state = await overridden_bus.get(event)
        if state is not None:
            await state.wait()
        return event, state

    @then("both decorators use the overridden bus")
    def test_overridden_bus(
        self, overridden_publication: tuple[Message, EventState[Message] | None]
    ) -> None:
        event, state = overridden_publication
        assert state is not None
        assert state.event is event
        successful, pending = state.result
        assert [result.value for result in successful] == [2]
        assert pending == []

    @when("a publisher and subscriber receive their declared dependencies")
    async def injected_publication(
        self, bus: EventBus
    ) -> EventState[Message] | None:
        def increment() -> int:
            return 2

        increment_dep: int = Depends(increment)

        @sub(Message, bus=bus)
        async def handler(event: Message, step: int = increment_dep) -> Message:
            return Message(value=event.value + step)

        @pub(bus=bus)
        async def produce(value: int = increment_dep) -> Message:
            return Message(value=value)

        state = await bus.get(await produce())
        if state is not None:
            await state.wait()
        return state

    @then("dependencies are injected into both event actions")
    def test_action_dependencies(
        self, injected_publication: EventState[Message] | None
    ) -> None:
        assert injected_publication is not None
        successful, pending = injected_publication.result
        assert [result.value for result in successful] == [4]
        assert pending == []


class TestScheduler:
    @when("a scheduled publisher runs and its scheduler context exits")
    async def publication_counts(self, bus: EventBus) -> tuple[int, int]:
        handled = asyncio.Event()

        @sub(Message, bus=bus)
        async def handler(event: Message) -> None:
            handled.set()

        @pub(bus=bus, on=timedelta(milliseconds=10))
        async def produce() -> Message:
            return Message(value=1)

        async with bus.scheduler():
            await asyncio.wait_for(handled.wait(), timeout=1)
        published = [state async for state in await bus.get(Message)]
        await asyncio.sleep(0.03)
        after_exit = [state async for state in await bus.get(Message)]
        return len(published), len(after_exit)

    @then("the scheduler publishes messages and stops on exit")
    def test_scheduler_stops(self, publication_counts: tuple[int, int]) -> None:
        published, after_exit = publication_counts
        assert published > 0
        assert after_exit == published
