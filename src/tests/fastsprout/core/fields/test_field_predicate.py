from asyncio import CancelledError, Event, create_task, gather
from collections.abc import AsyncIterator, Callable

import pytest

from fastsprout.core import BaseSchema, Field
from fastsprout.core.fields.conditions import And, Eq, Filter, Nand, Or, Xor
from fastsprout.core.fields.field_predicate import FieldPredicate, matches
from fastsprout.core.fields.field_ref import FieldComparison, FieldRef
from fastsprout.testing.core import given, then, when


class Record(BaseSchema):
    value: Field[int]


class TestFieldPredicate:
    @given("the record's integer field reference")
    def value_field(self) -> FieldRef[Record, int, None]:
        return Record.value

    @when("two field references are compared")
    def equality(
        self, value_field: FieldRef[Record, int, None]
    ) -> FieldComparison[Record, Record, int, None, None]:
        return value_field == Record.value

    @then("field equality retains its operands and reference identity")
    def test_field_equality(
        self,
        value_field: FieldRef[Record, int, None],
        equality: FieldComparison[Record, Record, int, None, None],
    ) -> None:
        field, comparison = value_field, equality
        other: FieldRef[Record, int, None] = FieldRef("other", Record, None)
        assert isinstance(comparison, FieldComparison)
        assert comparison.left is field
        assert comparison.right.name == "value"
        assert bool(comparison)
        assert not (field == other)
        assert hash(field) == hash(Record.value)
        assert field in {Record.value}
        assert (field == 1) is False

    @when(
        "a lazy membership predicate is evaluated concurrently and then reused"
    )
    async def membership(self) -> tuple[bool, list[bool], bool, list[int]]:
        consumed: list[int] = []

        async def values() -> AsyncIterator[int]:
            for value in (2, 7):
                consumed.append(value)
                yield value

        predicate = Record.value.in_(values())
        initially_empty = not consumed
        found = await gather(
            predicate(Record(value=2)), predicate(Record(value=7))
        )
        missing = await predicate(Record(value=4))
        return initially_empty, list(found), missing, consumed

    @then("membership consumes its source lazily and shares its values")
    def test_membership_is_lazy_and_shared(
        self, membership: tuple[bool, list[bool], bool, list[int]]
    ) -> None:
        initially_empty, found, missing, consumed = membership
        assert initially_empty
        assert found == [True, True]
        assert not missing
        assert consumed == [2, 7]

    @when("membership evaluation is cancelled while waiting for its source")
    async def cancelled_membership(self) -> tuple[CancelledError | None, bool]:
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
        try:
            await task
        except CancelledError as error:
            return error, closed.is_set()
        return None, closed.is_set()

    @then("cancelling membership closes its source")
    def test_cancelled_membership_closes_source(
        self, cancelled_membership: tuple[CancelledError | None, bool]
    ) -> None:
        failure, closed = cancelled_membership
        assert isinstance(failure, CancelledError)
        assert closed

    @given("a record with the requested value")
    def record(self, value: int) -> Record:
        return Record(value=value)

    @when("the field reference reads the record")
    def retrieved_value(self, record: Record) -> int:
        return Record.value(record)

    @then("a field reference reads its declared value as a stream getter")
    @pytest.mark.parametrize("value", [0, 7])
    def test_getter(self, retrieved_value: int, value: int) -> None:
        assert retrieved_value == value

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

    @when("the record is compared to an exclusive bound")
    async def compared(
        self,
        record: Record,
        comparison: Callable[[int], FieldPredicate[Record]],
    ) -> bool:
        return await comparison(5)(record)

    @pytest.mark.parametrize(
        "comparison, value, expected",
        [
            (Record.value.lt, 4, True),
            (Record.value.lt, 5, False),
            (Record.value.lt, 6, False),
            (Record.value.gt, 4, False),
            (Record.value.gt, 5, False),
            (Record.value.gt, 6, True),
        ],
    )
    @then("strict comparisons exclude their boundary")
    def test_strict_comparison(self, compared: bool, expected: bool) -> None:
        assert compared is expected

    @when("the source schema's visibility is read")
    def source_visibility(self, record: Record) -> str:
        return record.fastsprout_visibility

    @pytest.mark.parametrize("value", [1])
    @then("source schemas retain unrestricted entity visibility")
    def test_source_visibility(self, source_visibility: str) -> None:
        assert source_visibility == "entity"

    @when("the value is evaluated against composed conditions")
    async def composed_match(
        self, record: Record, condition: Filter[int]
    ) -> bool:
        return await matches(record.value, condition)

    @then("boolean groups preserve their identities and exclusive-or semantics")
    @pytest.mark.parametrize(
        "value, condition, expected",
        [
            (1, And(), True),
            (1, Or(), False),
            (1, Xor(), False),
            (1, Xor(Eq(1), Eq(2)), True),
            (1, Xor(Eq(1), Eq(1)), False),
            (1, Xor(Eq(2), Eq(3)), False),
            (1, Nand(Eq(1), Eq(2)), True),
            (1, Nand(Eq(1), Eq(1)), False),
            (1, 1, True),
            (1, 2, False),
        ],
    )
    def test_composed_conditions(
        self, composed_match: bool, expected: bool
    ) -> None:
        assert composed_match is expected
