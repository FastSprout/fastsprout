import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from bubus import EventBus as NativeBubusBus

from fastsprout.events import Event, EventBus, EventResult, sub
from fastsprout.events.backend.async_queue import AsyncQueueBroker
from fastsprout.events.backend.implementation import InMemoryBroker
from fastsprout.testing.core import then, when

from .base_test_broker import BaseTestBroker


class Message(Event):
    value: int


class TestInMemoryBroker(BaseTestBroker):
    @asynccontextmanager
    async def make_broker(self) -> AsyncIterator[InMemoryBroker]:
        broker = InMemoryBroker()
        try:
            yield broker
        finally:
            await broker.stop()


class TestAsyncQueueBroker(TestInMemoryBroker):
    @asynccontextmanager
    async def make_broker(self) -> AsyncIterator[AsyncQueueBroker]:
        broker = AsyncQueueBroker(asyncio.Queue[UUID](maxsize=1))
        try:
            yield broker
        finally:
            await broker.stop()

    @when("a handler publishes and awaits another queued event")
    async def nested_result(
        self, broker: AsyncQueueBroker
    ) -> EventResult[Message]:
        bus = EventBus(broker)

        @sub(Message, bus=bus)
        async def handler(event: Message) -> Message:
            if event.value == 1:
                child = await bus.publish(Message(value=2))
                await child.wait()
            return Message(value=event.value)

        async with asyncio.timeout(5):
            state = await bus.publish(Message(value=1))
            await broker.queue.join()
            return await state.wait()

    @then("nested publication completes without blocking the queue")
    def test_nested_publication(
        self, nested_result: EventResult[Message]
    ) -> None:
        done, pending = nested_result
        assert [item.value for item in done] == [1]
        assert pending == []

    @when("the queue is stopped with an unfinished handler")
    async def stopped_result(
        self, broker: AsyncQueueBroker
    ) -> EventResult[Message]:
        bus = EventBus(broker)
        entered = asyncio.Event()
        blocked = asyncio.Event()

        @sub(Message, bus=bus)
        async def handler(event: Message) -> None:
            entered.set()
            await blocked.wait()

        async with asyncio.timeout(5):
            state = await bus.publish(Message(value=1))
            await entered.wait()
            await broker.stop()
            await broker.queue.join()
            return await state.wait()

    @then("shutdown releases queue joins and cancels unfinished handlers")
    def test_shutdown(self, stopped_result: EventResult[Message]) -> None:
        done, pending = stopped_result
        assert done == []
        assert pending == []


async def test_in_memory_broker_collects_results_from_multiple_handlers():
    native = NativeBubusBus()
    bus = EventBus(InMemoryBroker(native))

    @sub(Message, bus=bus)
    async def first(event: Message) -> Message:
        return Message(value=event.value + 1)

    @sub(Message, bus=bus)
    async def second(event: Message) -> Message:
        return Message(value=event.value + 2)

    event = Message(value=1)
    state = await bus.publish(event)
    successful, pending = await state.wait()

    assert {result.value for result in successful} == {2, 3}
    assert pending == []
    assert await bus.get(event) is state
    assert native.handlers["FastSproutEnvelope"]


async def test_in_memory_broker_retracts_event_before_handlers_start():
    native = NativeBubusBus()
    bus = EventBus(InMemoryBroker(native))
    seen: list[Message] = []

    @sub(Message, bus=bus)
    async def handler(event: Message) -> None:
        seen.append(event)

    event = Message(value=1)
    state = await bus.publish(event)

    assert await bus.retract(state)
    await asyncio.sleep(0)

    assert seen == []
    assert await bus.get(event) is None


async def test_in_memory_broker_first_completed_keeps_other_result_pending():
    native = NativeBubusBus()
    bus = EventBus(InMemoryBroker(native))
    release = asyncio.Event()

    @sub(Message, bus=bus)
    async def slow(event: Message) -> Message:
        await release.wait()
        return Message(value=event.value + 1)

    @sub(Message, bus=bus)
    async def fast(event: Message) -> Message:
        return Message(value=event.value + 2)

    try:
        state = await bus.publish(Message(value=1))
        successful, pending = await state.wait(return_when="FIRST_COMPLETED")

        assert [result.value for result in successful] == [3]
        assert len(pending) == 1

        release.set()
        successful, pending = await state.wait()
        assert {result.value for result in successful} == {2, 3}
        assert pending == []
    finally:
        release.set()
