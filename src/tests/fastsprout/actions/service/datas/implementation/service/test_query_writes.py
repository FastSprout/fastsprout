import pytest

from fastsprout.actions import DataS
from fastsprout.core import Depends
from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.fields.field_predicate import FieldPredicate
from fastsprout.data import DataR, sql

from ...common import Record, Team


class TestQueryWrites:
    @pytest.mark.parametrize(
        "operation", ["update_by_query", "delete_by_query"]
    )
    async def test_query_and_separate_predicates_cannot_be_mixed(
        self, records: DataS[Record], operation: str
    ) -> None:
        # given
        created = await records.create(Record(name="Batman"))
        query = sql.SQLQuery(Record)
        # when / then
        with pytest.raises(TypeError, match="query or field predicates"):
            if operation == "update_by_query":
                await records.update_by_query(
                    query, Record.name.eq("Batman"), Record.score.set(20)
                )
            else:
                await records.delete_by_query(query, Record.name.eq("Batman"))
        stored = await records.get(created.id)
        assert stored is not None
        assert stored.score == created.score

    @pytest.mark.parametrize("use_lambda", [False, True])
    @pytest.mark.parametrize("additional", [False, True])
    async def test_selection_preserves_conditions_order_and_pagination(
        self, records: DataS[Record], use_lambda: bool, additional: bool
    ) -> None:
        # given
        await records.bulk_create(
            Record(name=str(score), score=score) for score in (10, 20, 30, 40)
        ).to_list()
        query = (
            sql.SQLQuery(Record)
            .where(
                (lambda row: row.score >= 20)
                if use_lambda
                else Record.score.gte(20)
            )
            .order_by(Record.score, reverse=True)
            .offset(1)
            .limit(1)
        )
        if additional:
            query = query.where(Record.score.lte(30))
        # when
        updated = await records.update_by_query(
            query, Record.note.set("changed")
        )
        rows = await records.find_all(
            sql.SQLQuery(Record).order_by(Record.score)
        )
        deleted = await records.delete_by_query(query)
        remaining = await records.find_all(
            sql.SQLQuery(Record).order_by(Record.score)
        )
        # then
        assert updated == deleted == 1
        assert [row.score for row in rows if row.note == "changed"] == [
            20 if additional else 30
        ]
        assert [row.score for row in remaining] == (
            [10, 30, 40] if additional else [10, 20, 40]
        )

    @pytest.mark.parametrize("name", ["id", "system_key", "missing"])
    async def test_forbidden_assignments_do_not_write(
        self, records: DataS[Record], name: str
    ) -> None:
        # given
        created = await records.create(Record(name="Batman"))
        query = sql.SQLQuery(Record)
        # when / then
        with pytest.raises(AttributeError, match="not writable"):
            await records.update_by_query(
                query.where(Record.score.gte(0)),
                FieldAssignment(name, "invalid"),
            )
        stored = await records.get(created.id)
        assert stored is not None
        assert stored.name == "Batman"
        assert stored.system_key == "system"

    @pytest.mark.parametrize("direct", [False, True])
    async def test_disabled_operations_and_empty_selection(
        self, records: DataS[Record], direct: bool
    ) -> None:
        # given
        query = Record.score.gte(20) if direct else sql.SQLQuery(Record)
        no_update = DataS(Record, update=None)
        no_delete = DataS(Record, operations=frozenset({"count"}))
        # when / then
        assert await records.update_by_query(query, Record.score.set(20)) == 0
        assert await records.delete_by_query(query) == 0
        with pytest.raises(AttributeError, match="disabled"):
            await no_update.update_by_query(query, Record.score.set(20))
        with pytest.raises(AttributeError, match="disabled"):
            await no_delete.delete_by_query(query)

    @pytest.mark.parametrize(
        "operation", ["update_by_query", "delete_by_query"]
    )
    async def test_dependency_rejection_prevents_the_write(
        self, records: DataS[Record], operation: str
    ) -> None:
        # given
        await records.create(Record(name="Batman"))
        calls: list[str] = []
        query = sql.SQLQuery(Record)

        def reject(operation: str, datar: DataR) -> None:
            assert datar is context
            calls.append(operation)
            raise PermissionError("Denied")

        service = DataS(Record, dependencies=[Depends(reject)])
        # when / then
        async with DataR() as context:
            with pytest.raises(PermissionError, match="Denied"):
                if operation == "update_by_query":
                    await service.update_by_query(
                        query.where(Record.name.eq("Batman")),
                        Record.score.set(20),
                        datar=context,
                    )
                else:
                    await service.delete_by_query(
                        query.where(Record.name.eq("Batman")), datar=context
                    )
            assert calls == [operation]
            found = await records.find_exactly_one(query, datar=context)
            assert found.name == "Batman"
            assert found.score == 10

    @pytest.mark.parametrize("direct", [False, True])
    @pytest.mark.parametrize(
        "predicates, expected",
        [
            ((), [10]),
            ((Record.score.lt(40),), [10, 40]),
            ((Record.score.lt(40), Record.name.ne("30")), [10, 30, 40]),
        ],
        ids=["one-condition", "two-conditions", "three-conditions"],
    )
    async def test_field_selection_updates_and_deletes_matches(
        self,
        records: DataS[Record],
        direct: bool,
        predicates: tuple[FieldPredicate[Record], ...],
        expected: list[int],
    ) -> None:
        # given
        await records.bulk_create(
            Record(name=str(score), score=score) for score in (10, 20, 30, 40)
        ).to_list()
        predicate = Record.score.gte(20)
        query = sql.SQLQuery(Record).where(predicate, *predicates)

        # when
        updated = (
            await records.update_by_query(
                predicate,
                Record.note.set("changed"),
                *predicates,
                Record.name.set("updated"),
            )
            if direct
            else await records.update_by_query(
                query, Record.note.set("changed"), Record.name.set("updated")
            )
        )
        changed = await records.find_all(
            sql.SQLQuery(Record).where(predicate, *predicates)
        )
        deleted = (
            await records.delete_by_query(predicate, *predicates)
            if direct
            else await records.delete_by_query(query)
        )
        remaining = await records.find_all(
            sql.SQLQuery(Record).order_by(Record.score)
        )

        # then
        assert updated == deleted == 4 - len(expected)
        assert {row.note for row in changed} == {"changed"}
        assert {row.name for row in changed} == {"updated"}
        assert [row.score for row in remaining] == expected
        assert query.conditions == (predicate, *predicates)

    @pytest.mark.parametrize(
        "operation", ["update_by_query", "delete_by_query"]
    )
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
    @pytest.mark.parametrize("additional", [False, True])
    async def test_field_selection_preserves_visibility_guards(
        self,
        records: DataS[Record],
        operation: str,
        predicate: FieldPredicate[Record] | FieldPredicate[Team],
        error: type[Exception],
        message: str,
        additional: bool,
    ) -> None:
        # given
        query = Record.score.gte(0) if additional else predicate
        predicates = (predicate,) if additional else ()
        created = await records.create(Record(name="Batman"))

        # when / then
        with pytest.raises(error, match=message):
            if operation == "update_by_query":
                await records.update_by_query(
                    query, Record.note.set("changed"), *predicates
                )
            else:
                await records.delete_by_query(query, *predicates)

        # then
        stored = await records.get(created.id)
        assert stored is not None
        assert stored.note == created.note
