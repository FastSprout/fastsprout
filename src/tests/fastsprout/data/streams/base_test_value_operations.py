from random import shuffle
from unittest.mock import Mock

from fastsprout.data.streams.implementation import SimpleAsyncValueStream
from fastsprout.data.types.valuable import HashableAndValuable

from .base_test_value_consumers import BaseTestValueConsumers
from .conftest import RANGE_START_END, make_async_range, make_range

__all__ = ["BaseTestValueOperations"]


class BaseTestValueOperations[T: HashableAndValuable](
    BaseTestValueConsumers[T]
):
    async def test_concat(self):
        # given
        value_stream: SimpleAsyncValueStream[T] = self.value_stream
        async_iterable = make_async_range(self.value_type)
        value_stream_async = SimpleAsyncValueStream(
            make_async_range(self.value_type)
        )
        sync_iterable = make_range(self.value_type)
        value_stream_sync = SimpleAsyncValueStream(make_range(self.value_type))
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
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.map(lambda item: item)
        # then
        assert await result.to_list() == list(make_range(self.value_type))

    async def test_filter(self):
        # given
        values = list(make_range(self.value_type))
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        keep = set(values[:3])
        # when
        result = value_stream.filter(lambda item: item in keep)
        # then
        assert await result.to_list() == values[:3]

    async def test_distinct(self):
        # given
        values = list(make_range(self.value_type))
        value_stream = SimpleAsyncValueStream(values + values)
        # when
        result = value_stream.distinct()
        # then
        assert await result.to_list() == values

    async def test_peek(self):
        # given
        mock = Mock(return_value=None)
        values = list(make_range(self.value_type))
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.peek(mock)
        # then
        assert await result.to_list() == values
        assert len(mock.call_args_list) == RANGE_START_END[1]

    async def test_take(self):
        # given
        values = list(make_range(self.value_type))
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.take(3)
        # then
        assert await result.to_list() == values[:3]

    async def test_take_minus(self):
        # given
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.take(-1)
        # then
        assert await result.to_list() == []

    async def test_take_zero(self):
        # given
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type, start=0, end=0)
        )
        # when
        result = value_stream.take(0)
        # then
        assert await result.to_list() == []

    async def test_drop(self):
        # given
        values = list(make_range(self.value_type))
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.drop(3)
        # then
        assert await result.to_list() == values[3:]

    async def test_take_while(self):
        # given
        values = list(make_range(self.value_type))
        limit = values[3]
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.take_while(lambda item: item < limit)
        # then
        assert await result.to_list() == values[:3]

    async def test_drop_while(self):
        # given
        values = list(make_range(self.value_type))
        limit = values[3]
        value_stream = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.drop_while(lambda item: item < limit)
        # then
        assert await result.to_list() == values[3:]

    async def test_sort_without_changes(self):
        # given
        values = list(make_range(self.value_type))
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.sort()
        # then
        assert await result.to_list() == values

    async def test_sort_revesed(self):
        # given
        values = list(make_range(self.value_type))[::-1]
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            self.range_generator(self.value_type)
        )
        # when
        result = value_stream.sort(reverse=True)
        # then
        assert await result.to_list() == values

    async def test_sort_shuffle(self):
        # given
        values = list(make_range(self.value_type))
        stream_values = list(make_range(self.value_type))
        shuffle(stream_values)
        value_stream: SimpleAsyncValueStream[T] = SimpleAsyncValueStream(
            stream_values
        )
        # when
        result = value_stream.sort()
        # then
        assert await result.to_list() == values

    async def test_sort_twice_first(self):
        # given
        value_stream = SimpleAsyncValueStream[T](
            self.range_generator(self.value_type)
        )
        # when
        result = await value_stream.sort().sort(reverse=True).first()
        # then
        assert float(result) == RANGE_START_END[1] - 1  # pyright: ignore[reportArgumentType]

    async def test_group_by_chained(self):
        # given
        value_stream = SimpleAsyncValueStream[T](
            self.range_generator(self.value_type)
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
            self.range_generator(self.value_type)
        )
        # when
        result = await value_stream.take(3).to_dict(
            lambda item: float(item),  # pyright: ignore[reportArgumentType]
            lambda item: float(item),  # pyright: ignore[reportArgumentType]
        )
        # then
        assert result == {0.0: 0.0, 1.0: 1.0, 2.0: 2.0}
