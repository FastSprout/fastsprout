from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import aclosing
from typing import assert_type

from fastsprout.core import Depends
from fastsprout.core.depends.invocation import stream_dependencies
from fastsprout.data.streams.implementation.base_common_stream import (
    BaseCommonStream,
)
from fastsprout.data.utils.iterable import resolve_any_iterable
from fastsprout.testing.core import then, when


class Numbers:
    def __aiter__(self) -> AsyncIterator[int]:
        return self

    async def __anext__(self) -> int:
        return 7


@when("an owner method is adapted to a stream and consumed")
async def owner_read() -> tuple[list[int], list[str]]:
    calls: list[str] = []

    def check() -> None:
        calls.append("check")

    class Source:
        dependencies = (Depends(check),)

        @BaseCommonStream.as_stream
        async def read(self) -> AsyncGenerator[int, None]:
            yield 7

    return await Source().read().to_list(), calls


@then("stream adapter does not run owner dependencies")
def test_stream_adapter_does_not_run_owner_dependencies(
    owner_read: tuple[list[int], list[str]],
) -> None:
    values, calls = owner_read
    assert values == [7]
    assert calls == []


@when("one chunk is consumed from a dependency-backed async iterable")
async def chunk_read() -> tuple[list[str], list[int], list[str], list[str]]:
    calls: list[str] = []

    async def resource() -> AsyncGenerator[int, None]:
        calls.append("open")
        try:
            yield 1
        finally:
            calls.append("close")

    @BaseCommonStream.as_stream
    @stream_dependencies
    def read(value: int = Depends(resource)) -> AsyncIterable[int]:
        assert value == 1
        return Numbers()

    stream = read()
    before = calls[:]
    async with aclosing(resolve_any_iterable(stream.chunked(2))) as chunks:
        chunk = await anext(chunks)
        assert_type(chunk, list[int])
        during = calls[:]
    return before, chunk, during, calls


@then("stream accepts async iterable and closes chunk dependencies")
def test_stream_accepts_async_iterable_and_closes_chunk_dependencies(
    chunk_read: tuple[list[str], list[int], list[str], list[str]],
) -> None:
    before, chunk, during, after = chunk_read
    assert before == []
    assert chunk == [7, 7]
    assert during == ["open"]
    assert after == ["open", "close"]


@when("a stream is closed after its first value")
async def stopped_read() -> tuple[int, bool]:
    closed = False

    @BaseCommonStream.as_stream
    async def read() -> AsyncGenerator[int, None]:
        nonlocal closed
        try:
            yield 1
            yield 2
        finally:
            closed = True

    async with aclosing(resolve_any_iterable(read())) as source:
        first = await anext(source)
    return first, closed


@then("stream closes source when stopped early")
def test_stream_closes_source_when_stopped_early(
    stopped_read: tuple[int, bool],
) -> None:
    first, closed = stopped_read
    assert first == 1
    assert closed
