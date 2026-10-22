import subprocess
import sys

import pytest

from fastsprout.testing.core import given, then, when


class TestOptionalDependencies:
    @given("an interpreter with one missing events dependency")
    def client(self) -> str:
        return """
import asyncio
import sys
from importlib.abc import MetaPathFinder

class WithoutDependency(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.partition('.')[0] == sys.argv[1]:
            raise ModuleNotFoundError('Dependency is not installed', name=sys.argv[1])

sys.meta_path.insert(0, WithoutDependency())

from fastsprout.events import Event, EventBus, EventState
from fastsprout.events.backend.implementation import InMemoryBroker

async def handler(event: Event) -> Event:
    return event

async def action() -> None:
    pass

async def main() -> None:
    broker = InMemoryBroker()
    bus = EventBus(broker)
    try:
        if sys.argv[1] == 'bubus':
            try:
                broker.native_bus()
            except ModuleNotFoundError as error:
                assert 'bubus' in str(error)
            else:
                raise AssertionError('Missing Bubus must be reported')
            broker.subscribe(Event, handler)
            state = EventState(Event())
            try:
                await broker.dispatch(state)
            except ModuleNotFoundError as error:
                assert 'bubus' in str(error)
            else:
                raise AssertionError('Dispatch must report missing Bubus')
            done, pending = await state.wait()
            assert done == [] and pending == []
            assert len(state.result.errors) == 1
            assert not broker.states and not broker.tasks and not broker.starts
        else:
            try:
                bus.schedule('* * * * *', action)
            except ModuleNotFoundError as error:
                assert 'cron' in str(error)
            else:
                raise AssertionError('Missing cron support must be reported')
        print('handled missing ' + sys.argv[1])
    finally:
        await broker.stop()

asyncio.run(main())
"""

    @when("the unavailable optional feature is requested")
    def checked(
        self, client: str, dependency: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-c", client, dependency],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )

    @pytest.mark.parametrize("dependency", ["bubus", "croniter"])
    @then(
        "the missing dependency is reported and incomplete work is cleaned up"
    )
    def test_missing_dependency(
        self, checked: subprocess.CompletedProcess[str], dependency: str
    ) -> None:
        assert checked.returncode == 0, checked.stdout + checked.stderr
        assert checked.stdout.strip() == f"handled missing {dependency}"
