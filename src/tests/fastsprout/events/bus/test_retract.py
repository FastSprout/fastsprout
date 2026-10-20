import asyncio

from fastsprout.events import EventBus, EventState
from fastsprout.testing.core import given, then, when

from ..backend.base_test_broker import Message


class TestRetraction:
    @given("a recorder of handled messages")
    def seen(self) -> list[Message]:
        return []

    @when("a published message is retracted before its handler starts")
    async def pending_retraction(
        self, bus: EventBus, seen: list[Message]
    ) -> tuple[bool, EventState[Message] | None]:
        async def handler(event: Message) -> None:
            seen.append(event)

        bus.subscribe(Message, handler)
        event = Message(value=1)
        state = await bus.publish(event)
        retracted = await bus.retract(state)
        await asyncio.sleep(0)
        return retracted, await bus.get(event)

    @then("retraction prevents dispatch and removes the stored state")
    def test_pending_handler(
        self,
        pending_retraction: tuple[bool, EventState[Message] | None],
        seen: list[Message],
    ) -> None:
        retracted, state = pending_retraction
        assert retracted
        assert state is None
        assert seen == []

    @when("retraction is attempted after a handler starts")
    async def running_retraction(self, bus: EventBus) -> bool:
        started = asyncio.Event()
        release = asyncio.Event()

        async def handler(event: Message) -> None:
            started.set()
            await release.wait()

        bus.subscribe(Message, handler)
        state = await bus.publish(Message(value=1))
        try:
            await asyncio.wait_for(started.wait(), timeout=1)
            return await bus.retract(state)
        finally:
            release.set()
            await state.wait()

    @then("a running handler cannot be retracted")
    def test_running_handler(self, running_retraction: bool) -> None:
        assert not running_retraction
