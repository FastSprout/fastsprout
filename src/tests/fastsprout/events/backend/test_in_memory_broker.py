import asyncio

from bubus import EventBus as NativeBubusBus

from fastsprout.events import Event, EventBus, sub
from fastsprout.events.backend.implementation import InMemoryBroker


class Message(Event):
    value: int


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
