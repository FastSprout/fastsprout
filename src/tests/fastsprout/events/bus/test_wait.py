import asyncio
from collections.abc import AsyncIterator

from fastsprout.events import EventBus, EventResult, EventState
from fastsprout.events.backend.in_memory import InMemoryBroker
from fastsprout.events.event import Eventable
from fastsprout.testing.core import given, then, when

from ..backend.base_test_broker import Completion, Message


class FutureBroker(InMemoryBroker):
    async def dispatch[E: Eventable](self, event_state: EventState[E]) -> None:
        future: asyncio.Future[Message] = (
            asyncio.get_running_loop().create_future()
        )
        event_state.result.add_pending(future)
        future.set_result(Message(value=3))


class TestWait:
    @given("two subscribers returning different results")
    def responding_bus(self, bus: EventBus) -> EventBus:
        async def first(event: Message) -> Message:
            return Message(value=event.value + 1)

        async def second(event: Message) -> Message:
            return Message(value=event.value + 2)

        bus.subscribe(Message, first)
        bus.subscribe(Message, second)
        return bus

    @when("all subscribers finish")
    async def completed(
        self, responding_bus: EventBus
    ) -> EventResult[Message, Message]:
        state = await responding_bus.publish(Message(value=1))
        return await state.wait()

    @then("wait collects both subscriber results without errors")
    def test_multiple_subscribers(
        self, completed: EventResult[Message, Message]
    ) -> None:
        successful, pending = completed
        assert {event.value for event in successful} == {2, 3}
        assert pending == []
        assert completed.errors == ()

    @when("a subscriber fails")
    async def failed(self, bus: EventBus) -> EventResult[Message, Message]:
        async def handler(event: Message) -> None:
            raise ValueError(event.value)

        bus.subscribe(Message, handler)
        state = await bus.publish(Message(value=1))
        return await state.wait(return_when="FIRST_EXCEPTION")

    @then("FIRST_EXCEPTION retains the handler error")
    def test_handler_errors(
        self, failed: EventResult[Message, Message]
    ) -> None:
        successful, pending = failed
        assert successful == []
        assert pending == []
        assert len(failed.errors) == 1
        assert isinstance(failed.errors[0], ValueError)

    @when("the fast subscriber finishes before the blocked subscriber")
    async def first_completion(
        self, bus: EventBus
    ) -> AsyncIterator[Completion]:
        release = asyncio.Event()

        async def slow(event: Message) -> Message:
            await release.wait()
            return Message(value=event.value + 1)

        async def fast(event: Message) -> Message:
            return Message(value=event.value + 2)

        bus.subscribe(Message, slow)
        bus.subscribe(Message, fast)
        state = await bus.publish(Message(value=1))
        successful, pending = await state.wait(return_when="FIRST_COMPLETED")
        try:
            yield Completion(
                state,
                release,
                tuple(event.value for event in successful),
                len(pending),
            )
        finally:
            release.set()
            await state.wait()

    @then("FIRST_COMPLETED keeps the remaining subscriber pending")
    def test_first_completed(self, first_completion: Completion) -> None:
        assert first_completion.values == (3,)
        assert first_completion.pending_count == 1

    @when("the pending subscriber is released")
    async def remaining_completion(
        self, first_completion: Completion
    ) -> EventResult[Message, Message]:
        first_completion.release.set()
        return await first_completion.state.wait()

    @then("a subsequent wait retains all results")
    def test_remaining_completion(
        self, remaining_completion: EventResult[Message, Message]
    ) -> None:
        successful, pending = remaining_completion
        assert {event.value for event in successful} == {2, 3}
        assert pending == []


class TestMultipleBrokers:
    @given("a second broker supplying a future result")
    async def multi_bus(
        self, broker: InMemoryBroker
    ) -> AsyncIterator[EventBus]:
        future_broker = FutureBroker()
        try:
            bus = EventBus(broker, future_broker)

            async def handler(event: Message) -> Message:
                return Message(value=event.value + 1)

            bus.subscribe(Message, handler)
            yield bus
        finally:
            await future_broker.stop()

    @when("both brokers complete their work")
    async def completed(
        self, multi_bus: EventBus
    ) -> EventResult[Message, Message]:
        state = await multi_bus.publish(Message(value=1))
        return await state.wait()

    @then("wait includes results registered by either broker")
    def test_other_broker_results(
        self, completed: EventResult[Message, Message]
    ) -> None:
        successful, pending = completed
        assert {event.value for event in successful} == {2, 3}
        assert pending == []
