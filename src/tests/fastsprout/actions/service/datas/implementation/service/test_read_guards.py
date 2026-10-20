import pytest

from fastsprout.actions import DataS
from fastsprout.core.depends.scope import dependency_resources
from fastsprout.core.fields.field_predicate import FieldPredicate
from fastsprout.data import sql
from fastsprout.testing.core import then, when

from ...common import Record, Team


class TestReadGuards:
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
