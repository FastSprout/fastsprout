import pytest

from fastsprout.actions import DataS
from fastsprout.core import Depends
from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.data import DataR, sql

from ...common import Record


class TestQueryWrites:
    @pytest.mark.parametrize("use_lambda", [False, True])
    async def test_selection_preserves_conditions_order_and_pagination(
        self, records: DataS[Record], use_lambda: bool
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
        assert [row.score for row in rows if row.note == "changed"] == [30]
        assert [row.score for row in remaining] == [10, 20, 40]

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
                query, FieldAssignment(name, "invalid")
            )
        stored = await records.get(created.id)
        assert stored is not None
        assert stored.name == "Batman"
        assert stored.system_key == "system"

    async def test_disabled_operations_and_empty_selection(
        self, records: DataS[Record]
    ) -> None:
        # given
        query = sql.SQLQuery(Record)
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
                        query, Record.score.set(20), datar=context
                    )
                else:
                    await service.delete_by_query(query, datar=context)
            assert calls == [operation]
            found = await records.find_exactly_one(query, datar=context)
            assert found.name == "Batman"
            assert found.score == 10
