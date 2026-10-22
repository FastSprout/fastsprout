from collections.abc import Awaitable, Callable
from decimal import Decimal
from types import NoneType
from typing import Any, cast

import pytest

from fastsprout.core.types.iterable import AnyIterable
from fastsprout.data.streams.implementation import SimpleAsyncValueStream
from fastsprout.data.types.valuable import HashableAndValuable

from .base_test_value_operations import BaseTestValueOperations
from .conftest import RANGE_START_END, make_async_range, make_range

__all__ = ["BaseTestSimpleAsyncValueStream"]


class BaseTestSimpleAsyncValueStream[T: HashableAndValuable](
    BaseTestValueOperations[T]
):
    @pytest.mark.parametrize(
        "stream_call, expected_result",
        [
            (
                lambda _, x: SimpleAsyncValueStream[T](x).all(
                    lambda x: bool(str(x))
                ),
                True,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .concat(
                        make_async_range(
                            type_,
                            start=RANGE_START_END[1],
                            end=RANGE_START_END[1] + 20,
                        ),
                    )
                    .concat(
                        make_async_range(
                            type_,
                            start=RANGE_START_END[1],
                            end=RANGE_START_END[1] + 20,
                        ),
                    )
                    .concat(
                        make_async_range(
                            type_,
                            start=RANGE_START_END[1],
                            end=RANGE_START_END[1] + 20,
                        ),
                    )
                    .count()
                ),
                RANGE_START_END[1] + 20 * 3,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .concat(
                        make_async_range(
                            type_,
                            start=RANGE_START_END[1] + 20,
                            end=RANGE_START_END[1] + 40,
                        ),
                        make_async_range(
                            type_,
                            start=RANGE_START_END[1],
                            end=RANGE_START_END[1] + 20,
                        ),
                    )
                    .sort()
                    .concat(
                        make_async_range(
                            type_,
                            start=RANGE_START_END[1],
                            end=RANGE_START_END[1] + 20,
                        )
                    )
                    .sort()
                    .sum_by(
                        lambda x: (
                            x
                            if isinstance(x, int | float | Decimal)
                            else float(x)  # type: ignore
                        )
                    )
                ),
                1615,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .sort()
                    .take(3)
                    .count()
                ),
                3,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .drop(2)
                    .take(5)
                    .count()
                ),
                5,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .concat(make_async_range(type_, *RANGE_START_END))
                    .distinct()
                    .count()
                ),
                RANGE_START_END[1],
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .sort()
                    .drop_while(lambda item: float(item) < 3)  # pyright: ignore[reportArgumentType]
                    .take_while(lambda item: float(item) < 7)  # pyright: ignore[reportArgumentType]
                    .count()
                ),
                4,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .filter(lambda item: bool(str(item)))
                    .map(lambda item: item)
                    .count()
                ),
                RANGE_START_END[1],
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .filter(lambda item: bool(str(item)))
                    .map(lambda item: item)
                    .any(lambda item: float(item) == 3)  # pyright: ignore[reportArgumentType]
                ),
                True,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .concat(make_async_range(type_, *RANGE_START_END))
                    .all(lambda item: float(item) < 5)  # pyright: ignore[reportArgumentType]
                ),
                False,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .sort()
                    .take(4)
                    .reduce(lambda item, acc: acc + float(item), 0.0)
                ),
                6.0,
            ),
            (
                lambda type_, x: (
                    SimpleAsyncValueStream[T](cast(AnyIterable[T], x))
                    .filter(lambda _: False)
                    .sort()
                    .map(lambda item: item)
                    .count()
                ),
                0,
            ),
        ],
    )
    async def test_stream_nested_call(
        self,
        stream_call: Callable[[type[T], AnyIterable[T]], Awaitable[Any]],
        expected_result,
    ):
        # given
        # when
        stream_result = await stream_call(
            self.value_type, self.range_generator(self.value_type)
        )
        # then
        assert stream_result == expected_result

    async def test_sum_by(self):
        # given
        value_stream = self.value_stream
        just_values = make_range(self.value_type)
        values_sum: T = (
            sum(list(just_values))  # pyright: ignore
            if issubclass(self.value_type, int | float | Decimal)
            else "".join(just_values)  # pyright: ignore
        )

        async def key(item: T) -> HashableAndValuable:
            return item

        # when
        result = await value_stream.sum_by(key)
        # then
        assert isinstance(result, self.value_type)
        assert values_sum == result

    async def test_sum_by_none(self):
        # given
        value_stream = SimpleAsyncValueStream([])

        async def key(item: T) -> HashableAndValuable:
            return item

        # when
        result = await value_stream.sum_by(key)
        # then
        assert isinstance(result, NoneType)

    async def test_sum(self):
        # given
        value_stream = self.value_stream
        just_values = make_range(self.value_type)
        values_sum: T = (
            sum(list(just_values))  # pyright: ignore
            if issubclass(self.value_type, int | float | Decimal)
            else "".join(just_values)  # pyright: ignore
        )
        # when
        result = await value_stream.sum()
        # then
        assert isinstance(result, self.value_type)
        assert values_sum == result

    async def test_sum_none(self):
        # given
        value_stream = SimpleAsyncValueStream([])
        # when
        result = await value_stream.sum()
        # then
        assert isinstance(result, NoneType)

    async def test_min(self):
        # given
        value_stream = self.value_stream
        just_values = list(make_range(self.value_type))
        values_min: T = (
            min(just_values)  # pyright: ignore
            if issubclass(self.value_type, int | float | Decimal)
            else just_values[0]  # pyright: ignore
        )

        async def key(item: T) -> HashableAndValuable:
            return item

        # when
        result = await value_stream.min(key)
        # then
        assert isinstance(result, self.value_type)
        assert values_min == result

    async def test_max(self):
        # given
        value_stream = self.value_stream
        just_values = list(make_range(self.value_type))
        values_max: T = (
            max(just_values)  # pyright: ignore
            if issubclass(self.value_type, int | float | Decimal)
            else just_values[-1]  # pyright: ignore
        )

        async def key(item: T) -> HashableAndValuable:
            return item

        # when
        result = await value_stream.max(key)
        # then
        assert isinstance(result, self.value_type)
        assert values_max == result
