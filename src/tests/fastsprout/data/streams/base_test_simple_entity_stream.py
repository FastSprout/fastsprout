from collections.abc import Awaitable, Callable
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

from fastsprout.core.types import AnyIterable
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream
from tests.fastsprout.data.streams.conftest import (
    RANGE_START_END,
    make_async_entity_range,
)

from .base_test_entity_operations import BaseTestEntityOperations

__all__ = ["BaseTestSimpleAsyncEntityStream"]


class BaseTestSimpleAsyncEntityStream[E: Entitieable](
    BaseTestEntityOperations[E]
):
    async def test_to_list(self):
        # given
        entity_stream = self.entity_stream
        # when
        result = await entity_stream.to_list()
        # then
        assert isinstance(result, list)
        assert len(result) == RANGE_START_END[1]
        for item in result:
            assert isinstance(item, self.entity_type)

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
            assert isinstance(call.args[0], self.entity_type)

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
        assert isinstance(result, self.entity_type)

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
            self.entity_builder, self.range_generator(self.entity_builder)
        )
        # then
        assert stream_result == expected_result
