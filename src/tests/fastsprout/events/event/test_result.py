import asyncio
from collections.abc import AsyncIterator

import pytest

from fastsprout.events import EventResult, EventState
from fastsprout.testing.core import given, then, when

from .common import Message, Reply


class TestResultRouting:
    @given("an event with pending reply and unrelated subscriber results")
    def state(self) -> EventState[Message]:
        return EventState(Message(value=1))

    @given("a reply view created before or after subscriber completion")
    def early_view(self, request: pytest.FixtureRequest) -> bool:
        return request.param

    @when("subscribers return a reply, a mixed sequence and unrelated data")
    async def routed(
        self, state: EventState[Message], early_view: bool
    ) -> EventResult[Message, Reply]:
        if early_view:
            state.result.route(Reply)
        for value in (Reply(value=2), [Reply(value=3), "other"], "other", None):
            future: asyncio.Future[Reply | list[Reply | str] | str | None] = (
                asyncio.get_running_loop().create_future()
            )
            state.result.add_pending(future)
            future.set_result(value)
        await state.wait()
        return await state.wait(Reply)

    @pytest.mark.parametrize("early_view", [True, False], indirect=True)
    @then("the view selects replies without changing the raw results")
    def test_selects_schema(
        self, state: EventState[Message], routed: EventResult[Message, Reply]
    ) -> None:
        done, pending = routed
        raw, _ = state.result
        assert done == [Reply(value=2), Reply(value=3)]
        assert raw == [
            Reply(value=2),
            [Reply(value=3), "other"],
            "other",
        ]
        assert routed is state.result.route(Reply)
        assert routed.route(Reply) is routed
        assert routed.state is state
        assert pending == []
        assert routed.errors == ()
        assert routed == routed
        assert routed != state.result
        assert len({routed, state.result}) == 2
        done.clear()
        retained, _ = routed
        assert retained == [Reply(value=2), Reply(value=3)]

    @when("an unrelated result finishes while a reply remains pending")
    async def timed_out(
        self, state: EventState[Message]
    ) -> tuple[EventResult[Message, Reply], asyncio.Future[Reply]]:
        unrelated: asyncio.Future[str] = (
            asyncio.get_running_loop().create_future()
        )
        reply: asyncio.Future[Reply] = (
            asyncio.get_running_loop().create_future()
        )
        state.result.add_pending(unrelated)
        state.result.add_pending(reply)
        unrelated.set_result("unrelated")
        result = await state.wait(
            Reply, return_when="FIRST_COMPLETED", timeout=0
        )
        return result, reply

    @then(
        "a schema timeout retains the pending future and returns no unrelated value"
    )
    def test_timeout(
        self,
        timed_out: tuple[EventResult[Message, Reply], asyncio.Future[Reply]],
    ) -> None:
        result, reply = timed_out
        done, pending = result
        assert done == []
        assert pending == [reply]
        assert not reply.cancelled()

    @when("the reply arrives after the first schema wait timed out")
    async def resumed(
        self,
        state: EventState[Message],
        timed_out: tuple[EventResult[Message, Reply], asyncio.Future[Reply]],
    ) -> EventResult[Message, Reply]:
        _, reply = timed_out
        reply.set_result(Reply(value=4))
        return await state.wait(Reply, return_when="FIRST_COMPLETED")

    @then("the same view receives the late reply")
    def test_resume(self, resumed: EventResult[Message, Reply]) -> None:
        done, pending = resumed
        assert done == [Reply(value=4)]
        assert pending == []

    @when("a subscriber fails before or after the view is created")
    async def failed(
        self, state: EventState[Message], early_view: bool
    ) -> EventResult[Message, Reply]:
        future: asyncio.Future[Reply] = (
            asyncio.get_running_loop().create_future()
        )
        state.result.add_pending(future)
        if early_view:
            state.result.route(Reply)
        future.set_exception(ValueError("subscriber failed"))
        await state.wait()
        return await state.wait(Reply, return_when="FIRST_EXCEPTION")

    @pytest.mark.parametrize("early_view", [True, False], indirect=True)
    @then("schema routing retains subscriber errors")
    def test_errors(self, failed: EventResult[Message, Reply]) -> None:
        done, pending = failed
        assert done == []
        assert pending == []
        assert len(failed.errors) == 1
        assert isinstance(failed.errors[0], ValueError)

    @when("an unrelated handler finishes before a delayed matching reply")
    async def first_reply(
        self, state: EventState[Message]
    ) -> EventResult[Message, Reply]:
        unrelated: asyncio.Future[str] = (
            asyncio.get_running_loop().create_future()
        )
        reply: asyncio.Future[Reply] = (
            asyncio.get_running_loop().create_future()
        )
        state.result.add_pending(unrelated)
        state.result.add_pending(reply)
        unrelated.set_result("ignored")
        asyncio.get_running_loop().call_later(
            0.01, reply.set_result, Reply(value=5)
        )
        return await state.wait(Reply, return_when="FIRST_COMPLETED")

    @then("FIRST_COMPLETED waits for the requested schema")
    def test_first_reply(
        self, first_reply: EventResult[Message, Reply]
    ) -> None:
        done, pending = first_reply
        assert done == [Reply(value=5)]
        assert pending == []

    @when("two callers await a reply while another handler remains pending")
    async def concurrent_waits(
        self, state: EventState[Message]
    ) -> AsyncIterator[list[EventResult[Message, Reply]]]:
        first: asyncio.Future[Reply] = (
            asyncio.get_running_loop().create_future()
        )
        second: asyncio.Future[Reply] = (
            asyncio.get_running_loop().create_future()
        )
        state.result.add_pending(first)
        state.result.add_pending(second)
        waiters = [
            asyncio.create_task(
                state.wait(Reply, return_when="FIRST_COMPLETED")
            )
            for _ in range(2)
        ]
        asyncio.get_running_loop().call_later(
            0.01, first.set_result, Reply(value=6)
        )
        try:
            yield await asyncio.wait_for(asyncio.gather(*waiters), timeout=1)
        finally:
            second.cancel()
            for waiter in waiters:
                waiter.cancel()
            await asyncio.gather(*waiters, return_exceptions=True)

    @then("both callers receive the first matching reply")
    def test_concurrent_waits(
        self, concurrent_waits: list[EventResult[Message, Reply]]
    ) -> None:
        assert len(concurrent_waits) == 2
        assert concurrent_waits[0] is concurrent_waits[1]
        done, pending = concurrent_waits[0]
        assert done == [Reply(value=6)]
        assert len(pending) == 1
