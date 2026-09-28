import asyncio
from datetime import timedelta

from fastsprout.core import Depends, inject_depends
from fastsprout.events import Event, EventBus, EventState, pub, sub
from fastsprout.events.backend.implementation import InMemoryBroker
from fastsprout.events.bus import get_default_event_bus
from fastsprout.events.event import Eventable
from fastsprout.events.middleware import EventsMiddleware


class Message(Event):
    value: int


def test_depends_uses_shared_default_event_bus():
    bus: EventBus = Depends()

    assert inject_depends.resolve(bus, EventBus) is get_default_event_bus()


async def test_event_ids_separate_events_of_the_same_type():
    bus = EventBus()
    first = Message(value=1)
    second = Message(value=1)

    assert first.__event_id__ != second.__event_id__
    assert first.__event_id__ == first.__event_id__
    assert "_event_id" not in first.model_dump()

    first_state = await bus.publish(first)
    second_state = await bus.publish(second)

    assert await bus.get(first) is first_state
    assert await bus.get(second) is second_state
    assert await bus.retract(first_state)
    assert await bus.get(first) is None
    assert await bus.get(second) is second_state


async def test_event_wrapper_reprs_show_events_and_results():
    bus = EventBus()

    @sub(Message, bus=bus)
    async def next_message(event: Message) -> Message:
        return Message(value=event.value + 1)

    first = Message(value=1)
    second = Message(value=2)
    first_state = await bus.publish(first)
    await bus.publish(second)
    group = await bus.get(first, second)
    result = await first_state.wait()

    assert repr(first_state) == "EventState(event=Message(value=1))"
    assert repr(group) == (
        "EventStatesGroup(EventState(event=Message(value=1)), "
        "EventState(event=Message(value=2)))"
    )
    assert repr(result) == (
        "EventResult(state=EventState(event=Message(value=1)), "
        "values=[Message(value=2)], pending=0, errors=[])"
    )


async def test_wait_collects_results_from_multiple_subscribers():
    bus = EventBus()

    @sub(Message, bus=bus)
    async def first(event: Message) -> Message:
        return Message(value=event.value + 1)

    @sub(Message, bus=bus)
    async def second(event: Message) -> Message:
        return Message(value=event.value + 2)

    state = await bus.publish(Message(value=1))

    successful, pending = await state.wait()

    assert {event.value for event in successful} == {2, 3}
    assert pending == []
    assert state.result._error_events == []


async def test_wait_collects_results_registered_by_another_broker():
    class FutureBroker(InMemoryBroker):
        async def dispatch[E: Eventable](
            self, event_state: EventState[E]
        ) -> None:
            future: asyncio.Future[Message] = (
                asyncio.get_running_loop().create_future()
            )
            event_state.result.add_pending(future)
            future.set_result(Message(value=3))

    bus = EventBus(InMemoryBroker(), FutureBroker())

    @sub(Message, bus=bus)
    async def handler(event: Message) -> Message:
        return Message(value=event.value + 1)

    state = await bus.publish(Message(value=1))
    successful, pending = await state.wait()

    assert {event.value for event in successful} == {2, 3}
    assert pending == []


async def test_first_completed_keeps_other_handlers_pending():
    bus = EventBus()
    release = asyncio.Event()

    @sub(Message, bus=bus)
    async def slow(event: Message) -> Message:
        await release.wait()
        return Message(value=event.value + 1)

    @sub(Message, bus=bus)
    async def fast(event: Message) -> Message:
        return Message(value=event.value + 2)

    state = await bus.publish(Message(value=1))

    await asyncio.sleep(0)
    await asyncio.sleep(0)
    successful, pending = await state.wait(return_when="FIRST_COMPLETED")
    assert [event.value for event in successful] == [3]
    assert len(pending) == 1

    release.set()
    successful, pending = await state.wait()
    assert {event.value for event in successful} == {2, 3}
    assert pending == []


async def test_wait_records_handler_errors():
    bus = EventBus()

    @sub(Message, bus=bus)
    async def handler(event: Message) -> None:
        raise ValueError(event.value)

    state = await bus.publish(Message(value=1))
    successful, pending = await state.wait(return_when="FIRST_EXCEPTION")

    assert successful == []
    assert pending == []
    assert len(state.result._error_events) == 1
    assert isinstance(state.result._error_events[0], ValueError)


async def test_retract_prevents_pending_handler_from_running():
    bus = EventBus()
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


async def test_retract_rejects_running_handler():
    bus = EventBus()
    started = asyncio.Event()
    release = asyncio.Event()

    @sub(Message, bus=bus)
    async def handler(event: Message) -> None:
        started.set()
        await release.wait()

    state = await bus.publish(Message(value=1))
    await started.wait()

    assert not await bus.retract(state)
    release.set()
    await state.wait()


async def test_pub_keeps_return_value_and_registers_event():
    bus = EventBus()

    @pub(bus=bus)
    async def produce() -> Message:
        return Message(value=1)

    event = await produce()

    assert (state := await bus.get(event)) is not None
    assert state.event is event


async def test_middleware_runs_for_annotated_event_type():
    seen: list[Message] = []

    class OtherMessage(Event): ...

    class Recorder:
        def __init__(self, bus: EventBus, /) -> None:
            self.bus = bus

        async def __call__(self, state: EventState[Message]) -> None:
            assert self.bus is bus
            result = await state.wait()
            assert result._success_events[0].value == 2
            seen.append(state.event)

    bus = EventBus(middleware=[EventsMiddleware(Recorder)])
    bus.add_middleware(Recorder)

    @sub(Message, bus=bus)
    async def handler(event: Message) -> Message:
        return Message(value=event.value + 1)

    await bus.publish(Message(value=1), OtherMessage())

    assert [event.value for event in seen] == [1, 1]


async def test_scheduler_runs_pub_action_and_stops_on_exit():
    bus = EventBus()
    handled = asyncio.Event()

    @sub(Message, bus=bus)
    async def handler(event: Message) -> None:
        handled.set()

    @pub(bus=bus, on=timedelta(milliseconds=10))
    async def produce() -> Message:
        return Message(value=1)

    async with bus.scheduler():
        await asyncio.wait_for(handled.wait(), timeout=1)

    states = await bus.get(Message)
    published = [state async for state in states]
    assert published
    await asyncio.sleep(0.03)
    states_after_exit = await bus.get(Message)
    assert len([state async for state in states_after_exit]) == len(published)


async def test_decorators_resolve_overridden_bus_dependency():
    bus = EventBus()

    @pub()
    async def produce() -> Message:
        return Message(value=1)

    inject_depends.dependency_overrides[EventBus] = lambda: bus
    try:

        @sub(Message)
        async def handler(event: Message) -> Message:
            return Message(value=event.value + 1)

        event = await produce()
        state = await bus.get(event)

        assert state is not None
        successful, pending = await state.wait()
        assert [result.value for result in successful] == [2]
        assert pending == []
    finally:
        del inject_depends.dependency_overrides[EventBus]


async def test_event_actions_inject_handler_and_publisher_dependencies():
    bus = EventBus()

    def increment() -> int:
        return 2

    increment_dep: int = Depends(increment)

    @sub(Message, bus=bus)
    async def handler(event: Message, step: int = increment_dep) -> Message:
        return Message(value=event.value + step)

    @pub(bus=bus)
    async def produce(value: int = increment_dep) -> Message:
        return Message(value=value)

    event = await produce()
    state = await bus.get(event)

    assert state is not None
    successful, pending = await state.wait()
    assert [result.value for result in successful] == [4]
    assert pending == []
