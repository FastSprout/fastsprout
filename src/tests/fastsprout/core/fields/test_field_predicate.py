from asyncio import CancelledError, Event, create_task, gather
from collections.abc import AsyncIterator

import pytest

from fastsprout.core import BaseSchema, Field


class Record(BaseSchema):
    value: Field[int]


class TestFieldPredicate:
    async def test_membership_is_lazy_and_shared(self) -> None:
        # given
        consumed: list[int] = []

        async def values() -> AsyncIterator[int]:
            for value in (2, 7):
                consumed.append(value)
                yield value

        predicate = Record.value.in_(values())
        assert consumed == []
        # when
        found = await gather(
            predicate(Record(value=2)), predicate(Record(value=7))
        )
        missing = await predicate(Record(value=4))
        # then
        assert found == [True, True]
        assert not missing
        assert consumed == [2, 7]

    async def test_cancelled_membership_closes_source(self) -> None:
        # given
        started = Event()
        closed = Event()
        pending = Event()

        async def values() -> AsyncIterator[int]:
            try:
                started.set()
                await pending.wait()
                yield 1
            finally:
                closed.set()

        predicate = Record.value.in_(values())
        # when
        task = create_task(predicate(Record(value=1)))
        await started.wait()
        task.cancel()
        # then
        with pytest.raises(CancelledError):
            await task
        assert closed.is_set()

    @pytest.mark.parametrize(
        "value, expected", [(4, False), (5, True), (10, True), (11, False)]
    )
    async def test_between_includes_endpoints(
        self, value: int, expected: bool
    ) -> None:
        # given
        predicate = Record.value.between(5, 10)
        # when
        found = await predicate(Record(value=value))
        # then
        assert found is expected
