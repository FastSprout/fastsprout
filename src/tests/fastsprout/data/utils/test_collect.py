from collections.abc import AsyncIterator, Callable, Sequence

import pytest

from fastsprout.data.exceptions import NotFoundError
from fastsprout.data.utils.collect import collect, collect_first, collect_one
from fastsprout.testing.core import given, then, when


class TestCollect:
    @when("an async generator is collected")
    async def collected(self) -> Sequence[int]:
        @collect
        async def values() -> AsyncIterator[int]:
            for value in range(3):
                yield value

        return await values()

    @then("collect preserves all values in order")
    def test_collect(self, collected: Sequence[int]) -> None:
        assert collected == [0, 1, 2]

    @given("a recorder of requested source chunk sizes")
    def sizes(self) -> list[int]:
        return []

    @given("a chunk source with or without values")
    def source(
        self, empty: bool, sizes: list[int]
    ) -> Callable[[], AsyncIterator[Sequence[int]]]:
        async def values(
            *, chunk_size: int = 10
        ) -> AsyncIterator[Sequence[int]]:
            sizes.append(chunk_size)
            yield []
            if not empty:
                yield [7, 8]

        return values

    @when("the first value is requested with optional or required semantics")
    async def first(
        self, source: Callable[[], AsyncIterator[Sequence[int]]], required: bool
    ) -> int | NotFoundError | None:
        try:
            return await (
                collect_one(source) if required else collect_first(source)
            )()
        except NotFoundError as error:
            return error

    @pytest.mark.parametrize("empty", [False, True])
    @pytest.mark.parametrize("required", [False, True])
    @then(
        "first-value collection skips empty chunks and distinguishes missing values"
    )
    def test_first(
        self,
        first: int | NotFoundError | None,
        empty: bool,
        required: bool,
        sizes: list[int],
    ) -> None:
        assert sizes == [1]
        if not empty:
            assert first == 7
        elif required:
            assert isinstance(first, NotFoundError)
        else:
            assert first is None
