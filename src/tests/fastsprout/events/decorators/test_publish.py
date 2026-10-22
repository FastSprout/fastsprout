import asyncio
from collections.abc import Awaitable, Callable, Sequence
from datetime import timedelta

import pytest

import fastsprout.events.bus as bus_module
from fastsprout.core import Depends, inject_depends
from fastsprout.events import EventBus, EventState, pub, sub
from fastsprout.events.bus import IN_MEMORY_EVENT_BUS
from fastsprout.testing.core import given, then, when

from ..backend.base_test_broker import Message


class TestPublisher:
    @given("a finite sequence of messages to publish")
    def messages(self, values: tuple[int, ...]) -> list[Message]:
        return [Message(value=value) for value in values]

    @when("a publisher returns the complete message sequence")
    async def published_sequence(
        self, bus: EventBus, messages: list[Message]
    ) -> tuple[Sequence[Message], list[EventState[Message] | None]]:
        @pub(bus=bus)
        async def produce() -> Sequence[Message]:
            return messages

        result = await produce()
        return result, [await bus.get(message) for message in messages]

    @pytest.mark.parametrize("values", [(), (1,), (1, 2)])
    @then("each returned message is published without replacing the sequence")
    def test_sequence(
        self,
        messages: list[Message],
        published_sequence: tuple[
            Sequence[Message], list[EventState[Message] | None]
        ],
    ) -> None:
        result, states = published_sequence
        assert result is messages
        assert all(state is not None for state in states)
        assert [
            state.event for state in states if state is not None
        ] == messages

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
    @when(
        "a scheduled action fails or cron support disappears after registration"
    )
    async def scheduler_failure(
        self,
        bus: EventBus,
        scheduled_action: tuple[asyncio.Event, Callable[[], Awaitable[None]]],
        missing: bool,
        monkeypatch: pytest.MonkeyPatch,
    ) -> ValueError | ModuleNotFoundError | None:
        called, action = scheduled_action

        async def fail() -> None:
            await action()
            raise ValueError("scheduled failure")

        bus.schedule(
            "* * * * *" if missing else timedelta(milliseconds=1), fail
        )
        if missing:
            monkeypatch.setattr(bus_module, "croniter", None)
        try:
            async with bus.scheduler():
                if missing:
                    await asyncio.sleep(0)
                else:
                    await asyncio.wait_for(called.wait(), timeout=1)
        except (ValueError, ModuleNotFoundError) as error:
            return error
        return None

    @pytest.mark.parametrize("missing", [False, True])
    @then("scheduler shutdown propagates the task failure")
    def test_scheduler_failure(
        self,
        missing: bool,
        scheduler_failure: ValueError | ModuleNotFoundError | None,
    ) -> None:
        expected = ModuleNotFoundError if missing else ValueError
        assert isinstance(scheduler_failure, expected)
        assert (
            "fastsprout[events]" if missing else "scheduled failure"
        ) in str(scheduler_failure)

    @given("a scheduled action recording its invocation")
    def scheduled_action(
        self,
    ) -> tuple[asyncio.Event, Callable[[], Awaitable[None]]]:
        called = asyncio.Event()

        async def run() -> None:
            called.set()

        return called, run

    @when("an invalid interval or cron expression is registered")
    def rejected_schedule(
        self,
        bus: EventBus,
        scheduled_action: tuple[asyncio.Event, Callable[[], Awaitable[None]]],
        schedule: str | timedelta,
    ) -> ValueError | None:
        try:
            bus.schedule(schedule, scheduled_action[1])
        except ValueError as error:
            return error
        return None

    @pytest.mark.parametrize(
        "schedule", [timedelta(), timedelta(seconds=-1), "invalid"]
    )
    @then("invalid schedules are rejected before starting the scheduler")
    def test_invalid_schedule(
        self, rejected_schedule: ValueError | None
    ) -> None:
        assert isinstance(rejected_schedule, ValueError)

    @when("cron scheduling is configured without its optional dependency")
    def missing_cron(
        self,
        bus: EventBus,
        scheduled_action: tuple[asyncio.Event, Callable[[], Awaitable[None]]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> ModuleNotFoundError | None:
        monkeypatch.setattr(bus_module, "croniter", None)
        try:
            bus.schedule("* * * * *", scheduled_action[1])
        except ModuleNotFoundError as error:
            return error
        return None

    @then("missing cron support identifies the required extra")
    def test_missing_cron(
        self, missing_cron: ModuleNotFoundError | None
    ) -> None:
        assert isinstance(missing_cron, ModuleNotFoundError)
        assert "fastsprout[events]" in str(missing_cron)

    @when("a real per-second cron schedule runs once")
    async def cron_delivery(
        self,
        bus: EventBus,
        scheduled_action: tuple[asyncio.Event, Callable[[], Awaitable[None]]],
    ) -> bool:
        called, action = scheduled_action
        bus.schedule("* * * * * *", action)
        async with bus.scheduler():
            await asyncio.wait_for(called.wait(), timeout=2)
        return called.is_set()

    @then("cron expressions execute the scheduled action")
    def test_cron_delivery(self, cron_delivery: bool) -> None:
        assert cron_delivery

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
