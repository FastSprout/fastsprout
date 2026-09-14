from collections.abc import Awaitable, Callable
from decimal import Decimal
from random import shuffle
from types import NoneType
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

from fastsprout.core.types.iterable import AnyIterable
from fastsprout.data.streams.implementation import SimpleAsyncValueStream
from fastsprout.data.types.valuable import HashableAndValuable
from fastsprout.data.utils.iterable import resolve_any_iterable

from .conftest import RANGE_START_END, make_async_range, make_range

__all__ = ["BaseTestSimpleAsyncValueStream"]


class BaseTestSimpleAsyncValueStream[T: HashableAndValuable]:
    __slots__ = ("_range_generator", "_type")

    _type: type[T]
    _range_generator: staticmethod

    @property
    def value_stream(self) -> SimpleAsyncValueStream[T]:
        return SimpleAsyncValueStream[T](self._range_generator(self._type))  # pyright: ignore[reportCallIssue]

    async def test_to_list(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        result = await value_stream.to_list()
        # then
        for item in result:
            assert isinstance(item, self._type)
        assert isinstance(result, list)

    async def test_to_set(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        result = await value_stream.to_set()
        # then
        for item in result:
            assert isinstance(item, self._type)

        assert isinstance(result, set)

    @pytest.mark.parametrize(
        "key, value, is_error",
        [
            (lambda x: x, lambda x: x, False),
            (lambda x: None, lambda x: None, False),
            (lambda x: 1, lambda x: 1, False),
            (lambda x: list(), lambda x: 1, True),
            (lambda x: object(), lambda x: 1, False),
            (lambda x: x, lambda x: [x], False),
            (lambda x: set(), lambda x: 1, True),
            (lambda x: x, lambda x: set([x]), False),
            (lambda x: (x,), lambda x: 1, False),
            (lambda x: (x,), lambda x: (x,), False),
        ],
    )
    async def test_to_dict(self, key, value, is_error):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        if is_error:
            with pytest.raises(TypeError):
                result = await value_stream.to_dict(key, value)
        else:
            result = await value_stream.to_dict(key, value)
            # then
            for _, _ in result.items():
                ...

            assert isinstance(result, dict)

    async def test_chunked(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        result = value_stream.chunked(size=3)
        # then
        iteration_number = 0
        async for chunk in result:
            assert isinstance(chunk, list)
            assert len(chunk) <= 3

            for item in chunk:
                assert isinstance(item, self._type)

            iteration_number += 1
        assert iteration_number == 4

    @pytest.mark.parametrize(
        "key, is_error",
        [
            (lambda x: x, False),
            (lambda x: None, False),
            (lambda x: list(), True),
            (lambda x: set(), True),
            (lambda x: object(), False),
        ],
    )
    async def test_group_by(self, key, is_error):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        if is_error:
            with pytest.raises(TypeError):
                result = await value_stream.group_by(key)
        else:
            result = await value_stream.group_by(key)
            # then
            for _, values in result.items():
                assert isinstance(values, list)
                for item in values:
                    assert isinstance(item, self._type)
            assert isinstance(result, dict)

    @pytest.mark.parametrize("mock", [Mock, AsyncMock])
    async def test_for_each(self, mock: type[Mock | AsyncMock]):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        call_mock = mock(return_value=None)
        # when
        await value_stream.for_each(call_mock)
        # then
        assert len(call_mock.call_args_list) == RANGE_START_END[1]
        for call in call_mock.call_args_list:
            assert len(call.args) == 1
            assert isinstance(call.args[0], self._type)  # pyright: ignore[reportArgumentType]

    async def test_reduce_to_accumulator(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream

        async def reducer(result, v):
            return result + v

        # when
        initial = self._type()
        result = await value_stream.reduce(reducer, initial)
        # then
        assert isinstance(result, self._type)
        assert result != initial

    async def test_reduce_to_list(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        initial: list[T] = []

        async def appender(v: T, result: list[T]) -> list[T]:
            return [*result, v]

        # when
        result: list[T] = await value_stream.reduce(appender, initial)  # pyright: ignore[reportArgumentType]
        # then
        assert isinstance(result, list)
        assert result != initial
        for item in result:
            assert isinstance(item, self._type)

    async def test_count(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        result: int = await value_stream.count()
        # then
        assert isinstance(result, int)
        assert result == RANGE_START_END[1]

    async def test_first(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        result = await value_stream.first()
        # then
        assert isinstance(result, self._type)
        assert result == next(make_range(self._type))

    async def test_first_none(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self._range_generator(self._type, start=0, end=0)
        )
        # when
        result = await value_stream.first()
        # then
        assert isinstance(result, NoneType)

    async def test_first_offset(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self._range_generator(self._type, start=0, end=2)
        )
        # when
        async for _ in value_stream:
            ...
        result = await value_stream.first()
        # then
        assert isinstance(result, NoneType)

    async def test_first_offset_with_second(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self._range_generator(self._type, start=0, end=2)
        )
        expected_value = None
        async for _expected_value in resolve_any_iterable(
            self._range_generator(self._type, start=1, end=2)
        ):
            expected_value = _expected_value
        # when
        async for _ in value_stream:
            break

        result = await value_stream.first()
        # then
        assert isinstance(result, self._type)
        assert result == expected_value

    async def test_all_true(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream

        async def predicate(item: T):
            return isinstance(item, self._type)

        # when
        result = await value_stream.all(predicate)
        # then
        assert result is True

    async def test_all_one_false(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self._range_generator(self._type, start=0, end=5)
        )
        bad_value = None
        async for _bad_value in resolve_any_iterable(
            self._range_generator(self._type, start=1, end=2)
        ):
            bad_value = _bad_value

        async def predicate(item: T) -> bool:
            return bad_value != item

        # when
        result = await value_stream.all(predicate)
        # then
        assert result is False

    async def test_any_true(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream

        async def predicate(item: T):
            return isinstance(item, self._type)

        # when
        result = await value_stream.all(predicate)
        # then
        assert result is True

    async def test_any_one_false(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self._range_generator(self._type, start=0, end=5)
        )
        bad_value = None
        async for _bad_value in resolve_any_iterable(
            self._range_generator(self._type, start=1, end=2)
        ):
            bad_value = _bad_value

        async def predicate(item: T) -> bool:
            return bad_value != item

        # when
        result = await value_stream.any(predicate)
        # then
        assert result is True

    async def test_any_all_false(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self._range_generator(self._type, start=5, end=10)
        )
        bad_value = None
        async for _bad_value in resolve_any_iterable(
            self._range_generator(self._type, start=1, end=2)
        ):
            bad_value = _bad_value

        async def predicate(item: T) -> bool:
            return bad_value == item

        # when
        result = await value_stream.any(predicate)
        # then
        assert result is False

    async def test_concat(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        async_iterable = make_async_range(self._type)
        value_stream_async = SimpleAsyncValueStream(
            make_async_range(self._type)
        )
        sync_iterable = make_range(self._type)
        value_stream_sync = SimpleAsyncValueStream(make_range(self._type))
        # when
        result = value_stream.concat(
            async_iterable, value_stream_async, sync_iterable, value_stream_sync
        )
        # then
        item_number = 0
        async for _ in result:
            item_number += 1
        assert item_number == (RANGE_START_END[1] * 5)

    async def test_map(self):
        # given
        value_stream = SimpleAsyncValueStream(self._range_generator(self._type))
        # when
        result = value_stream.map(lambda item: item)
        # then
        assert await result.to_list() == list(make_range(self._type))

    async def test_filter(self):
        # given
        values = list(make_range(self._type))
        value_stream = SimpleAsyncValueStream(self._range_generator(self._type))
        keep = set(values[:3])
        # when
        result = value_stream.filter(lambda item: item in keep)
        # then
        assert await result.to_list() == values[:3]

    async def test_distinct(self):
        # given
        values = list(make_range(self._type))
        value_stream = SimpleAsyncValueStream(values + values)
        # when
        result = value_stream.distinct()
        # then
        assert await result.to_list() == values

    async def test_peek(self):
        # given
        mock = Mock(return_value=None)
        values = list(make_range(self._type))
        value_stream = SimpleAsyncValueStream(self._range_generator(self._type))
        # when
        result = value_stream.peek(mock)
        # then
        assert await result.to_list() == values
        assert len(mock.call_args_list) == RANGE_START_END[1]

    async def test_take(self):
        # given
        values = list(make_range(self._type))
        value_stream = SimpleAsyncValueStream(self._range_generator(self._type))
        # when
        result = value_stream.take(3)
        # then
        assert await result.to_list() == values[:3]

    async def test_take_minus(self):
        # given
        value_stream = SimpleAsyncValueStream(self._range_generator(self._type))
        # when
        result = value_stream.take(-1)
        # then
        assert await result.to_list() == []

    async def test_take_zero(self):
        # given
        value_stream = SimpleAsyncValueStream(
            self._range_generator(self._type, start=0, end=0)
        )
        # when
        result = value_stream.take(0)
        # then
        assert await result.to_list() == []

    async def test_drop(self):
        # given
        values = list(make_range(self._type))
        value_stream = SimpleAsyncValueStream(self._range_generator(self._type))
        # when
        result = value_stream.drop(3)
        # then
        assert await result.to_list() == values[3:]

    async def test_take_while(self):
        # given
        values = list(make_range(self._type))
        limit = values[3]
        value_stream = SimpleAsyncValueStream(self._range_generator(self._type))
        # when
        result = value_stream.take_while(lambda item: item < limit)
        # then
        assert await result.to_list() == values[:3]

    async def test_drop_while(self):
        # given
        values = list(make_range(self._type))
        limit = values[3]
        value_stream = SimpleAsyncValueStream(self._range_generator(self._type))
        # when
        result = value_stream.drop_while(lambda item: item < limit)
        # then
        assert await result.to_list() == values[3:]

    async def test_sort_without_changes(self):
        # given
        values = list(make_range(self._type))
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self._range_generator(self._type)
        )
        # when
        result = value_stream.sort()
        # then
        assert await result.to_list() == values

    async def test_sort_revesed(self):
        # given
        values = list(make_range(self._type))[::-1]
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self._range_generator(self._type)
        )
        # when
        result = value_stream.sort(reverse=True)
        # then
        assert await result.to_list() == values

    async def test_sort_shuffle(self):
        # given
        values = list(make_range(self._type))
        stream_values = list(make_range(self._type))
        shuffle(stream_values)
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            stream_values
        )
        # when
        result = value_stream.sort()
        # then
        assert await result.to_list() == values

    async def test_sum_by(self):
        # given
        value_stream = self.value_stream
        just_values = make_range(self._type)
        values_sum: T = (
            sum(list(just_values))  # pyright: ignore
            if issubclass(self._type, int | float | Decimal)
            else "".join(just_values)  # pyright: ignore
        )

        async def key(item: T) -> HashableAndValuable:
            return item

        # when
        result = await value_stream.sum_by(key)
        # then
        assert isinstance(result, self._type)
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
        just_values = make_range(self._type)
        values_sum: T = (
            sum(list(just_values))  # pyright: ignore
            if issubclass(self._type, int | float | Decimal)
            else "".join(just_values)  # pyright: ignore
        )
        # when
        result = await value_stream.sum()
        # then
        assert isinstance(result, self._type)
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
        just_values = list(make_range(self._type))
        values_min: T = (
            min(just_values)  # pyright: ignore
            if issubclass(self._type, int | float | Decimal)
            else just_values[0]  # pyright: ignore
        )

        async def key(item: T) -> HashableAndValuable:
            return item

        # when
        result = await value_stream.min(key)
        # then
        assert isinstance(result, self._type)
        assert values_min == result

    async def test_max(self):
        # given
        value_stream = self.value_stream
        just_values = list(make_range(self._type))
        values_max: T = (
            max(just_values)  # pyright: ignore
            if issubclass(self._type, int | float | Decimal)
            else just_values[-1]  # pyright: ignore
        )

        async def key(item: T) -> HashableAndValuable:
            return item

        # when
        result = await value_stream.max(key)
        # then
        assert isinstance(result, self._type)
        assert values_max == result

    async def test_sort_twice_first(self):
        # given
        value_stream = SimpleAsyncValueStream[T](
            self._range_generator(self._type)
        )
        # when
        result = await value_stream.sort().sort(reverse=True).first()
        # then
        assert float(result) == RANGE_START_END[1] - 1  # pyright: ignore[reportArgumentType]

    async def test_group_by_chained(self):
        # given
        value_stream = SimpleAsyncValueStream[T](
            self._range_generator(self._type)
        )
        # when
        result = await value_stream.filter(
            lambda item: float(item) < 4  # pyright: ignore[reportArgumentType]
        ).group_by(lambda _: "all")
        # then
        assert len(result["all"]) == 4

    async def test_to_dict_chained(self):
        # given
        value_stream = SimpleAsyncValueStream[T](
            self._range_generator(self._type)
        )
        # when
        result = await value_stream.take(3).to_dict(
            lambda item: float(item),  # pyright: ignore[reportArgumentType]
            lambda item: float(item),  # pyright: ignore[reportArgumentType]
        )
        # then
        assert result == {0.0: 0.0, 1.0: 1.0, 2.0: 2.0}

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
            self._type, self._range_generator(self._type)
        )
        # then
        assert stream_result == expected_result
