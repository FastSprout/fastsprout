from typing import Any

import pytest

from fastsprout.core.types import AnyIterable
from fastsprout.data.utils.iterable import achain, chunked, resolve_any_iterable
from fastsprout.testing.core import given, then, when
from tests.fastsprout.data.conftest import ANY_ITERABLES


@pytest.mark.parametrize(
    "iterable",
    ANY_ITERABLES,
)
async def test_resolve_any_iterable(iterable: AnyIterable[Any]):
    # given
    # when
    aiterable = resolve_any_iterable(iterable)
    # then
    async for _ in aiterable:
        pass


async def test_achain(any_iterables):
    # given
    # when
    aiterable = achain(*any_iterables)
    # then
    async for _ in aiterable:
        pass


class TestChunked:
    @given("two input values")
    def values(self) -> list[int]:
        return [1, 2]

    @when("the input is divided into chunks of the requested size")
    async def chunks(
        self, values: list[int], size: int
    ) -> list[list[int]] | ValueError:
        try:
            return [chunk async for chunk in chunked(values, size)]
        except ValueError as error:
            return error

    @pytest.mark.parametrize(
        "size, expected",
        [(1, [[1], [2]]), (3, [[1, 2]]), (0, ValueError), (-1, ValueError)],
    )
    @then("positive sizes preserve values and nonpositive sizes are rejected")
    def test_sizes(
        self,
        chunks: list[list[int]] | ValueError,
        expected: list[list[int]] | type[ValueError],
    ) -> None:
        if isinstance(expected, type):
            assert isinstance(chunks, expected)
        else:
            assert chunks == expected
