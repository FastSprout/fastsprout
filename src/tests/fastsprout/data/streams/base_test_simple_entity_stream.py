from collections.abc import Awaitable, Callable, Generator
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

from fastsprout.core.types import AnyIterable
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from tests.fastsprout.data.streams.conftest import (
    RANGE_START_END,
    make_async_entity_range,
    make_entity_range,
)

__all__ = ["BaseTestSimpleAsyncEntityStream"]


class BaseTestSimpleAsyncEntityStream[E: Entitieable[Any]]:
    __slots__ = ("_entity_builder", "_entity_type", "_range_generator")

    _entity_type: type[E]
    _entity_builder: staticmethod
    _range_generator: staticmethod

    @property
    def entity_stream(self) -> SimpleAsyncEntityStream[E]:
        return SimpleAsyncEntityStream(
            self._range_generator(self._entity_builder)
        )  # pyright: ignore[reportCallIssue]

    async def test_concat(self):
        # given
        entity_stream = self.entity_stream
        async_iterable = make_async_entity_range(self._entity_builder)
        entity_stream_async = SimpleAsyncEntityStream(
            make_async_entity_range(self._entity_builder)
        )
        sync_iterable: Generator[E, None, None] = make_entity_range()  # pyright: ignore[reportAssignmentType]
        entity_stream_sync = SimpleAsyncEntityStream(
            make_entity_range(self._entity_builder)
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
        entities = list(make_entity_range(self._entity_builder))
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

    async def test_to_list(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.to_list()
        # then
        assert isinstance(result, list)
        assert len(result) == RANGE_START_END[1]
        for item in result:
            assert isinstance(item, self._entity_type)

    async def test_to_values(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = entity_stream.to_values(lambda entity: entity.id)
        # then
        assert len(await result.to_list()) == RANGE_START_END[1]

    async def test_to_dict(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.to_dict(
            lambda entity: entity.id, lambda entity: entity
        )
        # then
        assert isinstance(result, dict)
        assert len(result) == RANGE_START_END[1]

    async def test_chunked(self):
        # given
        entity_stream = self.entity_stream
        # when
        chunks = [chunk async for chunk in entity_stream.chunked(3)]
        # then
        assert len(chunks) == 4
        assert [len(chunk) for chunk in chunks] == [3, 3, 3, 1]

    async def test_group_by(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.group_by(lambda _: "all")
        # then
        assert list(result.keys()) == ["all"]
        assert len(result["all"]) == RANGE_START_END[1]

    @pytest.mark.parametrize("mock_class", [Mock, AsyncMock])
    async def test_for_each(self, mock_class: type[Mock] | type[AsyncMock]):
        # given
        mock = mock_class(return_value=None)
        entity_stream = self.entity_stream
        # when
        await entity_stream.for_each(mock)
        # then
        assert len(mock.call_args_list) == RANGE_START_END[1]
        for call in mock.call_args_list:
            assert len(call.args) == 1
            assert isinstance(call.args[0], self._entity_type)

    async def test_reduce(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.reduce(lambda _, acc: acc + 1, 0)  # pyright: ignore[reportOperatorIssue]
        # then
        assert result == RANGE_START_END[1]

    async def test_reduce_does_not_mutate_initial(self):
        # given
        entity_stream = self.entity_stream
        initial: list[E] = []
        # when
        result = await entity_stream.reduce(
            lambda item, acc: [*acc, item], initial
        )
        # then
        assert len(result) == RANGE_START_END[1]
        assert initial == []

    async def test_count(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.count()
        # then
        assert result == RANGE_START_END[1]

    async def test_first(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.first()
        # then
        assert isinstance(result, self._entity_type)

    async def test_first_empty(self):
        # given
        entity_stream = SimpleAsyncEntityStream[E]([])
        # when
        result = await entity_stream.first()
        # then
        assert result is None

    async def test_all(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.all(lambda _: True)
        # then
        assert result is True

    async def test_all_false(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.all(lambda _: False)
        # then
        assert result is False

    async def test_all_empty(self):
        # given
        entity_stream = SimpleAsyncEntityStream[E]([])
        # when
        result = await entity_stream.all(lambda _: False)
        # then
        assert result is True

    async def test_any(self):
        # given
        entity_stream = self.entity_stream
        index = 0

        def predicate(_) -> bool:
            nonlocal index
            index += 1
            return index == 3

        # when
        result = await entity_stream.any(predicate)
        # then
        assert result is True

    async def test_any_false(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.any(lambda _: False)
        # then
        assert result is False

    async def test_any_empty(self):
        # given
        entity_stream = SimpleAsyncEntityStream[E]([])
        # when
        result = await entity_stream.any(lambda _: True)
        # then
        assert result is False

    async def test_chained_lazy_await(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.filter(lambda _: True).take(5).count()
        # then
        assert result == 5

    async def test_sort(self):
        # given
        entities = list(make_entity_range(self._entity_builder))
        entity_stream = SimpleAsyncEntityStream(list(reversed(entities)))
        # when
        result = await entity_stream.sort(lambda entity: entity.id).to_list()
        # then
        assert [e.id for e in result] == sorted(e.id for e in entities)

    async def test_sort_reverse(self):
        # given
        entities = list(make_entity_range(self._entity_builder))
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
        entities = list(make_entity_range(self._entity_builder))
        entity_stream = SimpleAsyncEntityStream(list(reversed(entities)))

        async def key(entity: E) -> int:
            return entity.id

        # when
        result = await entity_stream.sort(key).to_list()
        # then
        assert [e.id for e in result] == sorted(e.id for e in entities)

    async def test_sort_stable_on_equal_keys(self):
        # given
        entities = list(make_entity_range(self._entity_builder))
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

    @pytest.mark.parametrize(
        "stream_call, expected_result",
        [
            (
                lambda _, x: SimpleAsyncEntityStream[E](x).all(
                    lambda entity: entity.id is not None
                ),
                True,
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .concat(make_async_entity_range(builder))
                    .concat(make_async_entity_range(builder))
                    .concat(make_async_entity_range(builder))
                    .count()
                ),
                RANGE_START_END[1] * 4,
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .sort(lambda entity: entity.id)
                    .take(3)
                    .count()
                ),
                3,
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .drop(2)
                    .take(5)
                    .count()
                ),
                5,
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .distinct()
                    .count()
                ),
                RANGE_START_END[1],
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .filter(lambda entity: entity.id is not None)
                    .map(lambda entity: entity)
                    .count()
                ),
                RANGE_START_END[1],
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .peek(lambda _: None)
                    .peek(lambda _: None)
                    .count()
                ),
                RANGE_START_END[1],
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .filter(lambda entity: entity.id is not None)
                    .map(lambda entity: entity)
                    .any(lambda entity: entity.id is not None)
                ),
                True,
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .concat(make_async_entity_range(builder))
                    .all(lambda entity: entity.id is None)
                ),
                False,
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .sort(lambda entity: entity.id)
                    .take(4)
                    .reduce(lambda _, acc: acc + 1, 0)  # pyright: ignore[reportOperatorIssue]
                ),
                4,
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .to_values(lambda entity: entity.id)
                    .distinct()
                    .count()
                ),
                RANGE_START_END[1],
            ),
            (
                lambda builder, x: (
                    SimpleAsyncEntityStream[E](cast(AnyIterable[E], x))
                    .filter(lambda _: False)
                    .sort(lambda entity: entity.id)
                    .map(lambda entity: entity)
                    .count()
                ),
                0,
            ),
        ],
    )
    async def test_stream_nested_call(
        self,
        stream_call: Callable[[Any, AnyIterable[E]], Awaitable[Any]],
        expected_result,
    ):
        # given
        # when
        stream_result = await stream_call(
            self._entity_builder, self._range_generator(self._entity_builder)
        )
        # then
        assert stream_result == expected_result
