from asyncio import Event as Signal
from asyncio import timeout
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager

from fastsprout.core import BaseSchema, dataclass
from fastsprout.events import (
    FIRST_COMPLETED,
    Event,
    EventBus,
    EventResult,
    EventState,
    sub,
)
from fastsprout.events.backend.in_memory import InMemoryBroker
from fastsprout.testing.core import given, then, when


class Message(Event):
    value: int


class Reply(BaseSchema):
    value: int


@dataclass
class Completion:
    state: EventState[Message]
    release: Signal
    values: tuple[int, ...]
    pending_count: int


class BaseTestBroker:
    def make_broker(self) -> AbstractAsyncContextManager[InMemoryBroker]:
        raise NotImplementedError

    @given("a real broker with automatic cleanup")
    async def broker(self) -> AsyncIterator[InMemoryBroker]:
        async with self.make_broker() as broker:
            yield broker

    @given("an EventBus using the broker adapter")
    def bus(self, broker: InMemoryBroker) -> EventBus:
        return EventBus(broker)

    @when("a message is published and all handlers finish")
    async def delivered(self, bus: EventBus) -> EventState[Message]:
        @sub(Message, bus=bus)
        async def handler(event: Message) -> Reply:
            return Reply(value=event.value + 1)

        async with timeout(15):
            state = await bus.publish(Message(value=1))
            await state.wait()
        return state

    @then("delivery preserves event identity and subscriber results")
    async def test_delivery(
        self, bus: EventBus, delivered: EventState[Message]
    ) -> None:
        done, pending = delivered.result
        assert [reply.value for reply in done] == [2]
        assert pending == []
        assert await bus.get(delivered.event) is delivered
        assert not await bus.retract(delivered)

    @when("only the fast handler finishes")
    async def first_completion(
        self, bus: EventBus
    ) -> AsyncIterator[Completion]:
        release = Signal()

        @sub(Message, bus=bus)
        async def fast(event: Message) -> Reply:
            return Reply(value=event.value)

        @sub(Message, bus=bus)
        async def slow(event: Message) -> Reply:
            await release.wait()
            return Reply(value=event.value + 1)

        async with timeout(15):
            state = await bus.publish(Message(value=1))
            done, pending = await state.wait(return_when=FIRST_COMPLETED)
        try:
            yield Completion(
                state,
                release,
                tuple(reply.value for reply in done),
                len(pending),
            )
        finally:
            release.set()
            async with timeout(15):
                await state.wait()

    @then("FIRST_COMPLETED leaves slow subscribers running")
    def test_wait(self, first_completion: Completion) -> None:
        assert first_completion.values == (1,)
        assert first_completion.pending_count == 1

    @when("the remaining subscriber is released")
    async def completed(
        self, first_completion: Completion
    ) -> EventResult[Message]:
        first_completion.release.set()
        async with timeout(15):
            return await first_completion.state.wait()

    @then("all subscriber results remain available after completion")
    def test_all_completed(self, completed: EventResult[Message]) -> None:
        done, pending = completed
        assert sorted(reply.value for reply in done) == [1, 2]
        assert pending == []

    @when("a handler rejects the published message")
    async def rejected(self, bus: EventBus) -> EventResult[Message]:
        @sub(Message, bus=bus)
        async def handler(event: Message) -> None:
            raise RuntimeError(f"rejected {event.value}")

        async with timeout(15):
            state = await bus.publish(Message(value=3))
            return await state.wait()

    @then("subscriber failures remain available on the event result")
    def test_handler_failure(self, rejected: EventResult[Message]) -> None:
        assert any(isinstance(error, RuntimeError) for error in rejected.errors)
        done, pending = rejected
        assert done == []
        assert pending == []

    @when("a handler is added between two publications")
    async def late_delivery(self, bus: EventBus) -> EventResult[Message]:
        async with timeout(15):
            first = await bus.publish(Message(value=1))
            await first.wait()

            @sub(Message, bus=bus)
            async def handler(event: Message) -> Reply:
                return Reply(value=event.value)

            second = await bus.publish(Message(value=2))
            return await second.wait()

    @then("late subscriptions start on the next dispatch")
    def test_late_subscription(
        self, late_delivery: EventResult[Message]
    ) -> None:
        done, pending = late_delivery
        assert [reply.value for reply in done] == [2]
        assert pending == []
