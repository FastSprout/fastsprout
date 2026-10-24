import asyncio

import pytest

from fastsprout.testing.container import container_context
from fastsprout.testing.core import given, then, when

from .common import RecordedContainer


class TestContainerContext:
    @given("a container whose startup can succeed or fail")
    def container(self, fail: bool) -> RecordedContainer:
        return RecordedContainer(fail=fail)

    @when("the container context is entered and exited")
    async def entered(
        self, container: RecordedContainer
    ) -> tuple[RecordedContainer | None, RuntimeError | None]:
        try:
            async with container_context(container) as active:
                return active, None
        except RuntimeError as error:
            return None, error

    @pytest.mark.parametrize("fail", [False, True])
    @then("containers are stopped after successful or failed startup")
    def test_cleanup(
        self,
        entered: tuple[RecordedContainer | None, RuntimeError | None],
        container: RecordedContainer,
        fail: bool,
    ) -> None:
        active, error = entered
        assert container.calls == ["start", "stop"]
        if fail:
            assert isinstance(error, RuntimeError)
            assert str(error) == "Startup failed"
        else:
            assert active is container
            assert error is None

    @given("a container paused during startup")
    def blocked(self) -> RecordedContainer:
        return RecordedContainer(blocked=True)

    @when("the context is cancelled while container startup is in progress")
    async def cancelled(self, blocked: RecordedContainer) -> bool:
        async def run() -> None:
            async with container_context(blocked):
                raise AssertionError("The cancelled context body was entered")

        task = asyncio.create_task(run())
        try:
            await asyncio.to_thread(blocked.started.wait)
            task.cancel()
            await asyncio.sleep(0)
        finally:
            blocked.release.set()
        try:
            await task
        except asyncio.CancelledError:
            return True
        return False

    @then("cancellation waits for startup before cleaning up the container")
    def test_cancellation(
        self, cancelled: bool, blocked: RecordedContainer
    ) -> None:
        assert cancelled
        assert blocked.calls == ["start", "stop"]
