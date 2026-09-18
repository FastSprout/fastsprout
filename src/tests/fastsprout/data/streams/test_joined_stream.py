import asyncio
from collections.abc import AsyncGenerator
from contextlib import aclosing

import pytest

from fastsprout.data.streams.implementation import JoinedStream


class Source[T]:
    def __init__(self, *items: T) -> None:
        self.items = items
        self.started = 0
        self.read = 0
        self.closed = 0

    def __aiter__(self) -> AsyncGenerator[T, None]:
        async def rows() -> AsyncGenerator[T, None]:
            self.started += 1
            try:
                for item in self.items:
                    self.read += 1
                    yield item
            finally:
                self.closed += 1

        return rows()


async def test_single_source_yields_singletons() -> None:
    source = Source(1, 2)
    stream = JoinedStream(source)
    pending = stream.to_list()
    assert source.started == 0
    assert await pending == [(1,), (2,)]
    assert source.closed == 1


async def test_inner_join_preserves_order_and_duplicate_matches() -> None:
    stream = JoinedStream(Source(2, 1, 2, 9)).join(
        Source((1, "a"), (2, "b"), (2, "c"), (7, "unused")),
        on=(lambda row: row[0], lambda item: item[0]),
    )
    assert await stream.to_list() == [
        (2, (2, "b")),
        (2, (2, "c")),
        (1, (1, "a")),
        (2, (2, "b")),
        (2, (2, "c")),
    ]


async def test_three_way_join_uses_any_previous_column_and_flat_tuples() -> (
    None
):
    stream = (
        JoinedStream(Source(1, 2))
        .join(Source("one", "two"), on=(lambda row: row[0], lambda s: 1))
        .join(
            Source(("two", 20), ("one", 10)),
            on=(lambda row: row[1], lambda item: item[0]),
        )
    )
    assert [row async for row in stream] == [
        (1, "one", ("one", 10)),
        (1, "two", ("two", 20)),
    ]


@pytest.mark.parametrize("left,right", [((), (1,)), ((1,), ()), ((1,), (2,))])
async def test_empty_or_unmatched_sources(left, right) -> None:
    stream = JoinedStream(Source(*left)).join(
        Source(*right), on=(lambda row: row[0], lambda item: item)
    )
    assert await stream.to_list() == []


async def test_none_is_an_ordinary_python_key() -> None:
    stream = JoinedStream(Source(None, 1)).join(
        Source(None), on=(lambda row: row[0], lambda item: item)
    )
    assert await stream.to_list() == [(None, None)]


async def test_lazy_indexing_and_early_close_release_upstream() -> None:
    left, right, third = Source(1, 2, 3), Source(1, 2), Source(1, 2)
    stream = (
        JoinedStream(left)
        .join(right, on=(lambda row: row[0], lambda item: item))
        .join(third, on=(lambda row: row[1], lambda item: item))
    )
    assert (left.started, right.started, third.started) == (0, 0, 0)
    async with aclosing(aiter(stream)) as iterator:
        assert await anext(iterator) == (1, 1, 1)
        assert left.read == 1
        assert right.read == third.read == 2
        assert right.closed == third.closed == 1
    assert left.closed == 1


async def test_extending_a_plan_keeps_other_branches_independent() -> None:
    base = JoinedStream(Source(1, 2))
    first = base.join(Source("a"), on=(lambda row: row[0], len))
    second = base.join(Source("bb"), on=(lambda row: row[0], len))
    assert await first.to_list() == [(1, "a")]
    assert await second.to_list() == [(2, "bb")]
    assert await base.to_list() == [(1,), (2,)]
    assert await first.to_list() == [(1, "a")]


@pytest.mark.parametrize("async_left", [True, False])
@pytest.mark.parametrize("async_right", [True, False])
async def test_sync_and_async_key_functions(async_left, async_right) -> None:
    async def left(row: tuple[int]) -> int:
        await asyncio.sleep(0)
        return row[0]

    async def right(item: str) -> int:
        await asyncio.sleep(0)
        return len(item)

    stream = JoinedStream(Source(1, 2)).join(
        Source("a", "bb"),
        on=(
            left if async_left else lambda row: row[0],
            right if async_right else len,
        ),
    )
    assert await stream.to_list() == [(1, "a"), (2, "bb")]


async def test_one_shot_sources_are_not_cached_or_replayed() -> None:
    stream = JoinedStream(aiter(Source(1))).join(
        aiter(Source(1)), on=(lambda row: row[0], lambda item: item)
    )
    assert await stream.to_list() == [(1, 1)]
    assert await stream.to_list() == []


async def test_callable_objects_and_returned_awaitables_are_resolved() -> None:
    class Key:
        async def __call__(self, item: str) -> int:
            return len(item)

    async def left(row: tuple[int]) -> int:
        return row[0]

    stream = JoinedStream(Source(1, 2)).join(
        Source("a", "bb"), on=(lambda row: left(row), Key())
    )
    assert await stream.to_list() == [(1, "a"), (2, "bb")]


async def test_iterator_without_aclose_is_supported() -> None:
    class Iterator:
        def __init__(self) -> None:
            self.items = iter([1, 2])

        def __aiter__(self):
            return self

        async def __anext__(self) -> int:
            try:
                return next(self.items)
            except StopIteration:
                raise StopAsyncIteration from None

    assert await JoinedStream(Iterator()).to_list() == [(1,), (2,)]


@pytest.mark.parametrize("side", ["left", "right"])
async def test_key_errors_propagate_and_close_open_sources(side) -> None:
    left, right = Source(1, 2), Source(1, 2)

    def fail(item) -> int:
        raise ValueError("bad key")

    stream = JoinedStream(left).join(
        right,
        on=(
            fail if side == "left" else lambda row: row[0],
            fail if side == "right" else lambda item: item,
        ),
    )
    with pytest.raises(ValueError, match="bad key"):
        await stream.to_list()
    assert right.closed == 1
    assert left.closed == (1 if side == "left" else 0)


@pytest.mark.parametrize("side", ["left", "right"])
async def test_source_errors_propagate_and_close_generators(side) -> None:
    closed = []

    async def broken():
        try:
            yield 1
            raise RuntimeError("source failed")
        finally:
            closed.append(True)

    stream = JoinedStream(broken() if side == "left" else Source(1)).join(
        broken() if side == "right" else Source(1),
        on=(lambda row: row[0], lambda item: item),
    )
    with pytest.raises(RuntimeError, match="source failed"):
        await stream.to_list()
    assert closed == [True]


@pytest.mark.parametrize("side", ["left", "right"])
async def test_cancellation_closes_active_source(side) -> None:
    started, closed = asyncio.Event(), asyncio.Event()

    async def blocking():
        try:
            started.set()
            await asyncio.Event().wait()
            yield 1
        finally:
            closed.set()

    stream = JoinedStream(blocking() if side == "left" else Source(1)).join(
        blocking() if side == "right" else Source(1),
        on=(lambda row: row[0], lambda item: item),
    )

    async def consume():
        return await stream.to_list()

    task = asyncio.create_task(consume())
    await asyncio.wait_for(started.wait(), timeout=2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert closed.is_set()


async def test_unhashable_keys_fail_at_runtime() -> None:
    stream = JoinedStream(Source(1)).join(
        Source(1), on=(lambda row: [], lambda item: [])
    )
    with pytest.raises(TypeError, match="unhashable"):
        await stream.to_list()
