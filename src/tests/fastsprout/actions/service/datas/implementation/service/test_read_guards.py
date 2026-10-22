from contextlib import aclosing

import pytest

from fastsprout.actions import DataS
from fastsprout.core.depends.scope import dependency_resources
from fastsprout.core.fields.field_predicate import FieldPredicate
from fastsprout.data import sql
from fastsprout.testing.core import then, when

from ...common import Record, Team


class TestReadGuards:
    @when("a join selects an internal field from either side")
    async def rejected_join(
        self, records: DataS[Record], left: bool
    ) -> AttributeError | None:
        fields = (
            (Record.system_key, Record.name)
            if left
            else (Record.name, Record.system_key)
        )
        try:
            async with aclosing(
                records.join(
                    sql.SQLQuery(Record), sql.SQLQuery(Record), on=fields
                )
            ) as rows:
                await anext(rows)
        except AttributeError as error:
            return error
        return None

    @pytest.mark.parametrize("left", [False, True])
    @then("joins cannot expose an internal field through their keys")
    def test_join_keys(self, rejected_join: AttributeError | None) -> None:
        assert isinstance(rejected_join, AttributeError)
        assert "Join field is not a public field" in str(rejected_join)
        assert dependency_resources.get() is None

    @when("a stream is requested with a foreign or internal field")
    async def rejected_stream(
        self,
        records: DataS[Record],
        predicate: FieldPredicate[Record] | FieldPredicate[Team],
        additional: bool,
    ) -> AttributeError | TypeError | None:
        first = Record.score.gte(0) if additional else predicate
        rest = (predicate,) if additional else ()
        try:
            await records.stream(first, *rest).to_list()
        except (AttributeError, TypeError) as error:
            return error
        return None

    @pytest.mark.parametrize("additional", [False, True])
    @pytest.mark.parametrize(
        "predicate, error, message",
        [
            (Team.name.eq("Batman"), TypeError, "belong to the service entity"),
            (
                Record.system_key.eq("system"),
                AttributeError,
                "not a public field",
            ),
        ],
        ids=["foreign-entity", "internal-field"],
    )
    @then(
        "read guards reject foreign and internal fields without leaking resources"
    )
    async def test_stream_field_guards(
        self,
        error: type[Exception],
        message: str,
        rejected_stream: AttributeError | TypeError | None,
    ) -> None:
        assert isinstance(rejected_stream, error)
        assert message in str(rejected_stream)
        assert dependency_resources.get() is None

    @when("a Query is combined with separate field predicates")
    async def rejected_reads(self, records: DataS[Record]) -> list[TypeError]:
        query = sql.SQLQuery(Record)
        failures: list[TypeError] = []
        try:
            await records.stream(query, Record.score.gte(20)).to_list()
        except TypeError as error:
            failures.append(error)
        try:
            await records.find_exactly_one(query, Record.score.gte(20))
        except TypeError as error:
            failures.append(error)
        return failures

    @then("read actions accept a Query or separate predicates")
    def test_reads_reject_query_with_separate_predicates(
        self, rejected_reads: list[TypeError]
    ) -> None:
        assert len(rejected_reads) == 2
        assert all(
            "query or field predicates" in str(error)
            for error in rejected_reads
        )
        assert dependency_resources.get() is None
