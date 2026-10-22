from types import NoneType
from unittest.mock import AsyncMock, Mock

import pytest

from fastsprout.data.streams.implementation import SimpleAsyncValueStream
from fastsprout.data.types.valuable import HashableAndValuable
from fastsprout.data.utils.iterable import resolve_any_iterable

from .conftest import RANGE_START_END, make_range

__all__ = ["BaseTestValueConsumers"]


class BaseTestValueConsumers[T: HashableAndValuable]:
    __slots__ = ("range_generator", "value_type")

    value_type: type[T]
    range_generator: staticmethod

    @property
    def value_stream(self) -> SimpleAsyncValueStream[T]:
        return SimpleAsyncValueStream[T](self.range_generator(self.value_type))  # pyright: ignore[reportCallIssue]

    async def test_to_list(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        result = await value_stream.to_list()
        # then
        for item in result:
            assert isinstance(item, self.value_type)
        assert isinstance(result, list)

    async def test_to_set(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        # when
        result = await value_stream.to_set()
        # then
        for item in result:
            assert isinstance(item, self.value_type)

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
                assert isinstance(item, self.value_type)

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
                    assert isinstance(item, self.value_type)
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
            assert isinstance(call.args[0], self.value_type)  # pyright: ignore[reportArgumentType]

    async def test_reduce_to_accumulator(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream

        async def reducer(result, v):
            return result + v

        # when
        initial = self.value_type()
        result = await value_stream.reduce(reducer, initial)
        # then
        assert isinstance(result, self.value_type)
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
            assert isinstance(item, self.value_type)

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
        assert isinstance(result, self.value_type)
        assert result == next(make_range(self.value_type))

    async def test_first_none(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self.range_generator(self.value_type, start=0, end=0)
        )
        # when
        result = await value_stream.first()
        # then
        assert isinstance(result, NoneType)

    async def test_first_offset(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self.range_generator(self.value_type, start=0, end=2)
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
            self.range_generator(self.value_type, start=0, end=2)
        )
        expected_value = None
        async for item in resolve_any_iterable(
            self.range_generator(self.value_type, start=1, end=2)
        ):
            expected_value = item
        # when
        async for _ in value_stream:
            break

        result = await value_stream.first()
        # then
        assert isinstance(result, self.value_type)
        assert result == expected_value

    async def test_all_true(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream

        async def predicate(item: T):
            return isinstance(item, self.value_type)

        # when
        result = await value_stream.all(predicate)
        # then
        assert result is True

    async def test_all_one_false(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self.range_generator(self.value_type, start=0, end=5)
        )
        bad_value = None
        async for item in resolve_any_iterable(
            self.range_generator(self.value_type, start=1, end=2)
        ):
            bad_value = item

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
            return isinstance(item, self.value_type)

        # when
        result = await value_stream.all(predicate)
        # then
        assert result is True

    async def test_any_one_false(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self.range_generator(self.value_type, start=0, end=5)
        )
        bad_value = None
        async for item in resolve_any_iterable(
            self.range_generator(self.value_type, start=1, end=2)
        ):
            bad_value = item

        async def predicate(item: T) -> bool:
            return bad_value != item

        # when
        result = await value_stream.any(predicate)
        # then
        assert result is True

    async def test_any_all_false(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self.range_generator(self.value_type, start=5, end=10)
        )
        bad_value = None
        async for item in resolve_any_iterable(
            self.range_generator(self.value_type, start=1, end=2)
        ):
            bad_value = item

        async def predicate(item: T) -> bool:
            return bad_value == item

        # when
        result = await value_stream.any(predicate)
        # then
        assert result is False
