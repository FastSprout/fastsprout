from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import aclosing
from typing import assert_type

from fastsprout.core import Depends
from fastsprout.core.depends.invocation import stream_dependencies
from fastsprout.data.streams.implementation.base_common_stream import (
    BaseCommonStream,
)
from fastsprout.data.utils.iterable import resolve_any_iterable
from fastsprout.testing.core import when_then


class Numbers:
    def __aiter__(self) -> AsyncIterator[int]:
        return self

    async def __anext__(self) -> int:
        return 7


@when_then("stream adapter does not run owner dependencies")
async def test_stream_adapter_does_not_run_owner_dependencies() -> None:
    calls: list[str] = []

    def check() -> None:
        calls.append("check")

    class Source:
        dependencies = (Depends(check),)

        @BaseCommonStream.as_stream
        async def read(self) -> AsyncGenerator[int, None]:
            yield 7

    assert await Source().read().to_list() == [7]
    assert calls == []


@when_then("stream accepts async iterable and closes chunk dependencies")
async def test_stream_accepts_async_iterable_and_closes_chunk_dependencies() -> (
    None
):
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
    assert calls == []
    async with aclosing(resolve_any_iterable(stream.chunked(2))) as chunks:
        chunk = await anext(chunks)
        assert_type(chunk, list[int])
        assert chunk == [7, 7]
        assert calls == ["open"]
    assert calls == ["open", "close"]


@when_then("stream closes source when stopped early")
async def test_stream_closes_source_when_stopped_early() -> None:
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
        assert await anext(source) == 1
    assert closed
