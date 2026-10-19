from asyncio import CancelledError, Event, create_task, gather
from collections.abc import AsyncIterator

import pytest

from fastsprout.core import BaseSchema, Field
from fastsprout.core.fields.field_ref import FieldComparison, FieldRef
from fastsprout.testing.core import given, then, when, when_then


class Record(BaseSchema):
    value: Field[int]


class TestFieldPredicate:
    @when_then("field equality retains its operands and reference identity")
    def test_field_equality(self) -> None:
        field = Record.value
        comparison = field == Record.value
        other: FieldRef[Record, int, None] = FieldRef("other", Record, None)
        assert isinstance(comparison, FieldComparison)
        assert comparison.left is field
        assert comparison.right.name == "value"
        assert bool(comparison)
        assert not (field == other)
        assert hash(field) == hash(Record.value)
        assert field in {Record.value}
        assert (field == 1) is False

    @when_then("membership consumes its source lazily and shares its values")
    async def test_membership_is_lazy_and_shared(self) -> None:
        consumed: list[int] = []

        async def values() -> AsyncIterator[int]:
            for value in (2, 7):
                consumed.append(value)
                yield value

        predicate = Record.value.in_(values())
        assert consumed == []
        found = await gather(
            predicate(Record(value=2)), predicate(Record(value=7))
        )
        missing = await predicate(Record(value=4))
        assert found == [True, True]
        assert not missing
        assert consumed == [2, 7]

    @when_then("cancelling membership closes its source")
    async def test_cancelled_membership_closes_source(self) -> None:
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
        task = create_task(predicate(Record(value=1)))
        await started.wait()
        task.cancel()
        with pytest.raises(CancelledError):
            await task
        assert closed.is_set()

    @given("a record with the requested value")
    def record(self, value: int) -> Record:
        return Record(value=value)

    @when("the record is checked against an inclusive range")
    async def within_range(self, record: Record) -> bool:
        return await Record.value.between(5, 10)(record)

    @then("the range includes both endpoints and excludes outside values")
    @pytest.mark.parametrize(
        "value, expected", [(4, False), (5, True), (10, True), (11, False)]
    )
    def test_between_includes_endpoints(
        self, within_range: bool, expected: bool
    ) -> None:
        assert within_range is expected
