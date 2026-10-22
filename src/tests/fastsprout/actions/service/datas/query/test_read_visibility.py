import pytest

from fastsprout.actions import DataS
from fastsprout.actions.service.datas.implementation.queries import (
    public_condition,
)
from fastsprout.core import ReadDTO
from fastsprout.data import DataR, sql
from fastsprout.data.capabilities.query import Eq
from fastsprout.data.capabilities.query.predicate import evaluate
from fastsprout.testing.core import given, then, when

from ..common import MemoryRecord, Record, Status


class ForeignRead(ReadDTO, MemoryRecord): ...


class TestReadVisibility:
    @when("a predicate projects into a DTO belonging to another entity")
    async def foreign_projection(self) -> TypeError | None:
        condition = public_condition(
            Record, ForeignRead, lambda record: record.name == "Batman"
        )
        try:
            await evaluate(condition, Record(name="Batman"))
        except TypeError as error:
            return error
        return None

    @then("the predicate cannot receive an unrelated entity's DTO")
    def test_projection_source(
        self, foreign_projection: TypeError | None
    ) -> None:
        assert isinstance(foreign_projection, TypeError)
        assert str(foreign_projection) == (
            "Read DTO must derive from the query entity"
        )

    @when("a comparison is used without specifying its entity field")
    async def rejected_comparison(
        self, records: DataS[Record], active_datar: DataR
    ) -> TypeError | None:
        def active(record: Record) -> bool:
            return record.status is Status.ACTIVE

        try:
            await records.count(
                sql.SQLQuery(Record).where(Eq(active)), datar=active_datar
            )
        except TypeError as error:
            return error
        return None

    @then("entity comparisons require a field or a callable predicate")
    def test_comparison_without_field(
        self, rejected_comparison: TypeError | None
    ) -> None:
        assert isinstance(rejected_comparison, TypeError)
        assert "field comparisons or predicates" in str(rejected_comparison)

    @given("a query ordered by a hidden entity field")
    def restricted_order(self, field_name: str) -> sql.SQLQuery[Record]:
        field = (
            Record.system_key if field_name == "system_key" else Record.password
        )
        return sql.SQLQuery(Record).order_by(field)

    @when("the service executes the restricted query")
    async def rejected_order(
        self,
        records: DataS[Record],
        active_datar: DataR,
        restricted_order: sql.SQLQuery[Record],
    ) -> AttributeError | None:
        try:
            await records.count(restricted_order, datar=active_datar)
        except AttributeError as error:
            return error
        return None

    @pytest.mark.parametrize("field_name", ["system_key", "password"])
    @then("sorting cannot expose internal or write-only fields")
    def test_hidden_order(self, rejected_order: AttributeError | None) -> None:
        assert isinstance(rejected_order, AttributeError)
        assert "Sort field is not a public field" in str(rejected_order)
