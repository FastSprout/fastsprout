from collections.abc import Generator
from unittest.mock import AsyncMock, Mock

import pytest

from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from tests.fastsprout.data.streams.conftest import (
    RANGE_START_END,
    make_async_entity_range,
    make_entity_range,
)

__all__ = ["BaseTestEntityOperations"]


class BaseTestEntityOperations[E: Entitieable]:
    __slots__ = ("entity_builder", "entity_type", "range_generator")

    entity_type: type[E]
    entity_builder: staticmethod
    range_generator: staticmethod

    @property
    def entity_stream(self) -> SimpleAsyncEntityStream[E]:
        return SimpleAsyncEntityStream(
            self.range_generator(self.entity_builder)
        )  # pyright: ignore[reportCallIssue]

    async def test_concat(self):
        # given
        entity_stream = self.entity_stream
        async_iterable = make_async_entity_range(self.entity_builder)
        entity_stream_async = SimpleAsyncEntityStream(
            make_async_entity_range(self.entity_builder)
        )
        sync_iterable: Generator[E, None, None] = make_entity_range()  # pyright: ignore[reportAssignmentType]
        entity_stream_sync = SimpleAsyncEntityStream(
            make_entity_range(self.entity_builder)
        )
        # when
        result = entity_stream.concat(
            async_iterable,
            entity_stream_async,
            sync_iterable,
            entity_stream_sync,
        )
        # then
        item_number = 0
        async for _ in result:
            item_number += 1
        assert item_number == (RANGE_START_END[1] * 5)

    async def test_map(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.map(lambda entity: entity)
        # then
        assert len(await result.to_list()) == RANGE_START_END[1]

    async def test_filter(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.filter(lambda _: True)
        # then
        assert len(await result.to_list()) == RANGE_START_END[1]

    async def test_filter_all_out(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.filter(lambda _: False)
        # then
        assert len(await result.to_list()) == 0

    async def test_distinct(self):
        # given
        entities = list(make_entity_range(self.entity_builder))
        entity_stream = SimpleAsyncEntityStream(entities + entities)
        # when
        result = entity_stream.distinct()
        # then
        assert len(await result.to_list()) == RANGE_START_END[1]

    @pytest.mark.parametrize("mock_class", [Mock, AsyncMock])
    async def test_peek(self, mock_class: type[Mock] | type[AsyncMock]):
        # given
        mock = mock_class(return_value=None)
        entity_stream = self.entity_stream
        # when
        result = entity_stream.peek(mock)
        # then
        assert len(await result.to_list()) == RANGE_START_END[1]
        assert len(mock.call_args_list) == RANGE_START_END[1]

    async def test_take(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.take(3)
        # then
        assert len(await result.to_list()) == 3

    async def test_take_minus(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.take(-1)
        # then
        assert len(await result.to_list()) == 0

    async def test_take_more_than_available(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.take(RANGE_START_END[1] + 10)
        # then
        assert len(await result.to_list()) == RANGE_START_END[1]

    async def test_drop(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.drop(3)
        # then
        assert len(await result.to_list()) == RANGE_START_END[1] - 3

    async def test_drop_more_than_available(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.drop(RANGE_START_END[1] + 10)
        # then
        assert len(await result.to_list()) == 0

    async def test_take_while(self):
        # given
        entity_stream = self.entity_stream
        index = 0

        def predicate(_) -> bool:
            nonlocal index
            index += 1
            return index <= 3

        # when
        result = entity_stream.take_while(predicate)
        # then
        assert len(await result.to_list()) == 3

    async def test_drop_while(self):
        # given
        entity_stream = self.entity_stream
        index = 0

        def predicate(_) -> bool:
            nonlocal index
            index += 1
            return index <= 3

        # when
        result = entity_stream.drop_while(predicate)
        # then
        assert len(await result.to_list()) == RANGE_START_END[1] - 3

    async def test_chained_lazy_await(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.filter(lambda _: True).take(5).count()
        # then
        assert result == 5

    async def test_sort(self):
        # given
        entities = list(make_entity_range(self.entity_builder))
        entity_stream = SimpleAsyncEntityStream(list(reversed(entities)))
        # when
        result = await entity_stream.sort(lambda entity: entity.id).to_list()
        # then
        assert [e.id for e in result] == sorted(e.id for e in entities)

    async def test_sort_reverse(self):
        # given
        entities = list(make_entity_range(self.entity_builder))
        entity_stream = SimpleAsyncEntityStream(entities)
        # when
        result = await entity_stream.sort(
            lambda entity: entity.id, reverse=True
        ).to_list()
        # then
        assert [e.id for e in result] == sorted(
            (e.id for e in entities), reverse=True
        )

    async def test_sort_with_async_key(self):
        # given
        entities = list(make_entity_range(self.entity_builder))
        entity_stream = SimpleAsyncEntityStream(list(reversed(entities)))

        async def key(entity: E) -> int:
            return entity.id

        # when
        result = await entity_stream.sort(key).to_list()
        # then
        assert [e.id for e in result] == sorted(e.id for e in entities)

    async def test_sort_stable_on_equal_keys(self):
        # given
        entities = list(make_entity_range(self.entity_builder))
        entity_stream = SimpleAsyncEntityStream(entities)
        # when
        result = entity_stream.sort(lambda _: 0)
        # then
        assert await result.to_list() == entities

    async def test_sort_empty(self):
        # given
        entity_stream = SimpleAsyncEntityStream[E]([])
        # when
        result = entity_stream.sort(lambda entity: entity.id)
        # then
        assert await result.to_list() == []

    async def test_to_values(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.to_values(lambda entity: entity.id)
        # then
        assert len(await result.to_list()) == RANGE_START_END[1]
