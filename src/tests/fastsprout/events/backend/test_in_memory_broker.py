import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import pytest
from bubus import EventBus as NativeBubusBus

from fastsprout.events import EventBus, EventResult, EventState, sub
from fastsprout.events.backend.async_queue import AsyncQueueBroker
from fastsprout.events.backend.implementation import InMemoryBroker
from fastsprout.testing.core import given, then, when

from .base_test_broker import BaseTestBroker, Completion, Message


class TestInMemoryBroker(BaseTestBroker):
    @asynccontextmanager
    async def make_broker(self) -> AsyncIterator[InMemoryBroker]:
        broker = InMemoryBroker(NativeBubusBus())
        try:
            yield broker
        finally:
            await broker.stop()

    @when("two native Bubus handlers finish processing a message")
    async def native_delivery(self, bus: EventBus) -> EventState[Message]:
        @sub(Message, bus=bus)
        async def first(event: Message) -> Message:
            return Message(value=event.value + 1)

        @sub(Message, bus=bus)
        async def second(event: Message) -> Message:
            return Message(value=event.value + 2)

        state = await bus.publish(Message(value=1))
        await state.wait()
        return state

    @then("native Bubus collects both results and retains the event state")
    async def test_collects_results_from_multiple_handlers(
        self,
        broker: InMemoryBroker,
        bus: EventBus,
        native_delivery: EventState[Message],
    ) -> None:
        successful, pending = native_delivery.result
        assert {result.value for result in successful} == {2, 3}
        assert pending == []
        assert await bus.get(native_delivery.event) is native_delivery
        assert broker.bus is not None
        assert broker.bus.handlers["FastSproutEnvelope"]

    @when("a native Bubus message is retracted before handlers start")
    async def retracted(
        self, bus: EventBus
    ) -> tuple[bool, list[Message], EventState[Message] | None]:
        seen: list[Message] = []

        @sub(Message, bus=bus)
        async def handler(event: Message) -> None:
            seen.append(event)

        event = Message(value=1)
        state = await bus.publish(event)
        removed = await bus.retract(state)
        await asyncio.sleep(0)
        return removed, seen, await bus.get(event)

    @then("retraction removes the event and prevents native handlers running")
    def test_retracts_event_before_handlers_start(
        self,
        retracted: tuple[bool, list[Message], EventState[Message] | None],
    ) -> None:
        removed, seen, state = retracted
        assert removed
        assert seen == []
        assert state is None

    @when(
        "a native Bubus event is awaited before and after releasing a handler"
    )
    async def native_completions(
        self, bus: EventBus
    ) -> tuple[Completion, EventResult[Message, Message]]:
        release = asyncio.Event()

        @sub(Message, bus=bus)
        async def slow(event: Message) -> Message:
            await release.wait()
            return Message(value=event.value + 1)

        @sub(Message, bus=bus)
        async def fast(event: Message) -> Message:
            return Message(value=event.value + 2)

        state = await bus.publish(Message(value=1))
        successful, pending = await state.wait(return_when="FIRST_COMPLETED")
        first = Completion(
            state,
            release,
            tuple(result.value for result in successful),
            len(pending),
        )
        release.set()
        return first, await state.wait()

    @then("FIRST_COMPLETED preserves pending work and both eventual results")
    def test_first_completed_keeps_other_result_pending(
        self,
        native_completions: tuple[Completion, EventResult[Message, Message]],
    ) -> None:
        first, completed = native_completions
        assert first.values == (3,)
        assert first.pending_count == 1
        successful, pending = completed
        assert {result.value for result in successful} == {2, 3}
        assert pending == []


class TestAsyncQueueBroker(BaseTestBroker):
    @asynccontextmanager
    async def make_broker(self) -> AsyncIterator[AsyncQueueBroker]:
        broker = AsyncQueueBroker(asyncio.Queue[UUID](maxsize=1))
        try:
            yield broker
        finally:
            await broker.stop()

    @given("a consumer paused while its bounded queue is full")
    def paused_consumer(
        self, broker: AsyncQueueBroker, monkeypatch: pytest.MonkeyPatch
    ) -> asyncio.Event:
        entered = asyncio.Event()
        release = asyncio.Event()

        async def consume() -> None:
            entered.set()
            await release.wait()

        monkeypatch.setattr(broker, "consume", consume)
        return entered

    @when("a blocked publication is cancelled and the queue is stopped")
    async def cancelled_publication(
        self, broker: AsyncQueueBroker, paused_consumer: asyncio.Event
    ) -> tuple[bool, bool, bool, bool]:
        queued = EventState(Message(value=1))
        broker.prepare(queued)
        broker.queue.put_nowait(queued.event.__event_id__)
        blocked = EventState(Message(value=2))
        task = asyncio.create_task(broker.dispatch(blocked))
        cancelled = False
        async with asyncio.timeout(5):
            await paused_consumer.wait()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                cancelled = True
            removed = await broker.get(blocked.event) is None
            await broker.stop()
            await broker.queue.join()
            _, pending = await blocked.wait()
        return cancelled, removed, broker.queue.empty(), not pending

    @then("cancellation retracts the event and shutdown drains queued IDs")
    def test_cancelled_publication(
        self, cancelled_publication: tuple[bool, bool, bool, bool]
    ) -> None:
        assert cancelled_publication == (True, True, True, True)

    @when("a handler publishes and awaits another queued event")
    async def nested_result(
        self, broker: AsyncQueueBroker
    ) -> EventResult[Message, Message]:
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
        self, nested_result: EventResult[Message, Message]
    ) -> None:
        done, pending = nested_result
        assert [item.value for item in done] == [1]
        assert pending == []

    @when("the queue is stopped with an unfinished handler")
    async def stopped_result(
        self, broker: AsyncQueueBroker
    ) -> EventResult[Message, Message]:
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
    def test_shutdown(
        self, stopped_result: EventResult[Message, Message]
    ) -> None:
        done, pending = stopped_result
        assert done == []
        assert pending == []
