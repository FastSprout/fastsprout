from collections.abc import AsyncGenerator, Generator

import pytest

from fastsprout.core import Depends, inject_depends
from fastsprout.core.depends.invocation import with_dependencies


async def test_async_yield_provider_closes_after_invocation() -> None:
    calls: list[str] = []

    async def resource() -> AsyncGenerator[int, None]:
        calls.append("open")
        try:
            yield 7
        finally:
            calls.append("close")

    @with_dependencies
    async def read(value: int = Depends(resource)) -> int:
        calls.append("read")
        return value

    assert await read() == 7
    assert calls == ["open", "read", "close"]


async def test_sync_yield_provider_receives_action_exception() -> None:
    calls: list[str] = []

    def resource() -> Generator[int, None, None]:
        try:
            yield 7
        except ValueError:
            calls.append("rollback")
            raise
        else:
            calls.append("commit")

    @with_dependencies
    async def execute(value: int = Depends(resource)) -> int:
        raise ValueError("Abort")

    with pytest.raises(ValueError, match="Abort"):
        await execute()
    assert calls == ["rollback"]


async def test_injected_resource_is_cached_and_closed_per_invocation() -> None:
    calls: list[str] = []

    def resource() -> Generator[int, None, None]:
        calls.append("open")
        try:
            yield 7
        finally:
            calls.append("close")

    @inject_depends
    async def execute(
        first: int = Depends(resource), second: int = Depends(resource)
    ) -> int:
        calls.append("execute")
        return first + second

    assert await execute() == 14
    assert calls == ["open", "execute", "close"]
    assert await execute() == 14
    assert calls == ["open", "execute", "close"] * 2
