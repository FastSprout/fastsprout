from collections.abc import AsyncIterator
from contextlib import aclosing
from uuid import uuid4

import pytest
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from fastsprout.actions import DataS
from fastsprout.core import Depends, inject_depends
from fastsprout.core.depends.scope import dependency_resources
from fastsprout.core.fields.field_predicate import FieldPredicate
from fastsprout.data import DataR, sql
from fastsprout.data.utils.iterable import resolve_any_iterable
from fastsprout.testing.core import when_then

from ...common import Record, RecordRead, RecordWrite, Team


class TestReads:
    @pytest.mark.parametrize("direct", [False, True])
    @pytest.mark.parametrize("additional", [False, True])
    async def test_stream_conditions_preserve_read_dtos(
        self, records: DataS[Record], direct: bool, additional: bool
    ) -> None:
        # given
        await records.bulk_create(
            Record(name=name, score=score)
            for name, score in (("Batman", 10), ("Robin", 20), ("Batgirl", 30))
        ).to_list()
        service = DataS(Record, read=RecordRead)
        predicate = Record.score.gte(20)
        predicates = (Record.name.eq("Robin"),) if additional else ()
        query = sql.SQLQuery(Record).where(predicate, *predicates)
        # when
        rows = await (
            service.stream(predicate, *predicates)
            if direct
            else service.stream(query)
        ).to_list()
        # then
        assert {row.name for row in rows} == (
            {"Robin"} if additional else {"Robin", "Batgirl"}
        )
        assert all(isinstance(row, RecordRead) for row in rows)
        for row in rows:
            with pytest.raises(AttributeError):
                row.__getattribute__("system_key")
        assert query.conditions == (predicate, *predicates)

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
    async def test_stream_field_guards(
        self,
        records: DataS[Record],
        predicate: FieldPredicate[Record] | FieldPredicate[Team],
        error: type[Exception],
        message: str,
        additional: bool,
    ) -> None:
        # given
        first = Record.score.gte(0) if additional else predicate
        rest = (predicate,) if additional else ()
        # when / then
        with pytest.raises(error, match=message):
            await records.stream(first, *rest).to_list()
        assert dependency_resources.get() is None

    @when_then("read actions accept a Query or separate predicates")
    async def test_reads_reject_query_with_separate_predicates(
        self, records: DataS[Record]
    ) -> None:
        query = sql.SQLQuery(Record)
        with pytest.raises(TypeError, match="query or field predicates"):
            await records.stream(query, Record.score.gte(20)).to_list()
        with pytest.raises(TypeError, match="query or field predicates"):
            await records.find_exactly_one(query, Record.score.gte(20))
        assert dependency_resources.get() is None

    @when_then("Query and direct predicates preserve the read DTO")
    @pytest.mark.parametrize("direct", [False, True])
    async def test_read_dtos_preserve_query_order_and_pagination(
        self, records: DataS[Record], direct: bool
    ) -> None:
        service = DataS(Record, read=RecordRead)
        await records.bulk_create(
            Record(name=name, score=score)
            for name, score in (("Batman", 10), ("Robin", 20), ("Batgirl", 30))
        ).to_list()
        query = sql.SQLQuery(Record).order_by(Record.score).offset(1).limit(1)
        first = await service.find_first(query)
        only = await (
            service.find_exactly_one(
                Record.name.eq("Robin"), Record.score.eq(20)
            )
            if direct
            else service.find_exactly_one(query)
        )
        all_rows = await service.find_all(query)
        streamed = await service.stream(query).to_list()
        assert first is not None
        for row in (first, only, *all_rows, *streamed):
            assert isinstance(row, RecordRead)
            assert row.name == "Robin"
            with pytest.raises(AttributeError):
                row.__getattribute__("system_key")
        assert len(all_rows) == len(streamed) == 1

    @when_then("exact matches reject zero or multiple results")
    @pytest.mark.parametrize("direct", [False, True])
    async def test_empty_and_multiple_results(
        self, records: DataS[Record], direct: bool
    ) -> None:
        query = sql.SQLQuery(Record)
        selection = Record.score.gte(0) if direct else query
        assert await records.find_first(query) is None
        assert await records.find_all(query) == []
        assert await records.stream(query).to_list() == []
        assert await records.stream(Record.score.gte(20)).to_list() == []
        with pytest.raises(NoResultFound):
            await records.find_exactly_one(selection)
        await records.bulk_create(
            Record(name=name) for name in ("a", "b")
        ).to_list()
        with pytest.raises(MultipleResultsFound):
            await records.find_exactly_one(selection)

    @pytest.mark.parametrize("direct", [False, True])
    @pytest.mark.parametrize("stop_early", [False, True])
    async def test_stream_is_lazy_and_closes_dependency_scope(
        self,
        records: DataS[Record],
        monkeypatch: pytest.MonkeyPatch,
        stop_early: bool,
        direct: bool,
    ) -> None:
        # given
        await records.bulk_create(
            Record(name=name) for name in ("a", "b")
        ).to_list()
        lifecycle: list[str] = []

        async def provide() -> AsyncIterator[DataR]:
            lifecycle.append("open")
            try:
                async with DataR() as datar:
                    yield datar
            finally:
                lifecycle.append("close")

        def check(operation: str, datar: DataR) -> None:
            assert operation == "stream"
            assert isinstance(datar, DataR)
            lifecycle.append("check")

        monkeypatch.setitem(inject_depends.dependency_providers, DataR, provide)
        service = DataS(Record, dependencies=[Depends(check)])
        # when
        stream = (
            service.stream(Record.score.eq(10), Record.name.ne("missing"))
            if direct
            else service.stream(sql.SQLQuery(Record).order_by(Record.name))
        )
        assert lifecycle == []
        async with aclosing(resolve_any_iterable(stream)) as rows:
            assert (await anext(rows)).name == "a"
            assert lifecycle == ["open", "check"]
            if not stop_early:
                assert [row.name async for row in rows] == ["b"]
        # then
        assert lifecycle == ["open", "check", "close"]
        assert dependency_resources.get() is None

    async def test_read_none_disables_all_query_read_actions(
        self, records: DataS[Record]
    ) -> None:
        # given
        service = DataS(Record, read=None)
        query = sql.SQLQuery(Record)
        # when / then
        with pytest.raises(AttributeError, match="disabled"):
            await service.find_first(query)
        with pytest.raises(AttributeError, match="disabled"):
            await service.find_exactly_one(query)
        with pytest.raises(AttributeError, match="disabled"):
            await service.find_all(query)
        with pytest.raises(AttributeError, match="disabled"):
            service.stream(query)
        with pytest.raises(AttributeError, match="disabled"):
            service.stream(Record.score.gte(20))
        with pytest.raises(AttributeError, match="disabled"):
            service.map(query, lambda row: row)
        with pytest.raises(AttributeError, match="disabled"):
            service.join(query, query, on=(Record.id, Record.id))

    @pytest.mark.parametrize("native", [False, True])
    async def test_list_total_and_count_ignore_pagination(
        self, records: DataS[Record], native: bool
    ) -> None:
        # given
        await records.bulk_create(
            Record(name=str(score), score=score) for score in (20, 30, 40)
        ).to_list()
        query = (
            sql.SQLQuery(Record)
            .where(
                Record.score.gte(20) if native else lambda row: row.score >= 20
            )
            .order_by(Record.score, reverse=True)
            .offset(1)
            .limit(1)
        )
        # when
        page = await records.list(query)
        count = await records.count(query)
        empty = await records.list(query.copy().limit(0))
        # then
        assert [row.score for row in page.items] == [30]
        assert (page.total, page.offset, page.limit) == (3, 1, 1)
        assert count == empty.total == 3
        assert empty.items == []
        assert (query.offset_value, query.limit_value) == (1, 1)

    async def test_explicit_write_and_read_dtos_preserve_visibility(
        self, records: DataS[Record]
    ) -> None:
        # given
        service = DataS(Record, create=RecordWrite, read=RecordRead)
        payload = service.create_schema(name="Batman", password="secret")
        # when
        created = await service.create(payload)
        stored = await records.get(created.id)
        # then
        assert isinstance(payload, RecordWrite)
        assert "id" not in vars(payload)
        assert isinstance(created, RecordRead)
        assert created.name == "Batman"
        assert stored is not None and stored.password == "secret"
        with pytest.raises(AttributeError, match="not accessible"):
            service.create_schema(id=created.id, name="Robin")
        for name in ("password", "system_key"):
            assert name not in vars(created)
            with pytest.raises(AttributeError, match="not accessible"):
                created.__getattribute__(name)

    async def test_exists_checks_the_key_before_and_after_delete(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        missing = uuid4()
        # when / then
        async with DataR() as datar:
            assert await records.exists(missing, datar=datar) is False
            created = await records.create(Record(name="Batman"), datar=datar)
            assert await records.exists(created.id, datar=datar) is True
            await records.delete(created.id, datar=datar)
            assert await records.exists(created.id, datar=datar) is False

    async def test_exists_has_an_independent_operation_switch(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        operations: list[str] = []

        def observe(operation: str) -> None:
            operations.append(operation)

        service = DataS(
            Record,
            dependencies=[Depends(observe)],
            operations=frozenset({"exists"}),
        )
        # when / then
        async with DataR() as datar:
            created = await records.create(Record(name="Batman"), datar=datar)
            assert await service.exists(created.id, datar=datar) is True
            service.operations = frozenset()
            with pytest.raises(AttributeError, match="disabled"):
                await service.exists(created.id, datar=datar)
        assert operations == ["exists"]
