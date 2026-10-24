import logging
from contextlib import aclosing

import pytest

from fastsprout.actions import DataS
from fastsprout.core import Depends, ReadDTO
from fastsprout.core.depends.scope import dependency_resources
from fastsprout.data import DataR, sql
from fastsprout.data.capabilities.query import Eq, where

from ...common import Record, RecordRead


class TestJoin:
    async def test_field_join_uses_sql_and_explicit_read_schema(
        self, records: DataS[Record], caplog: pytest.LogCaptureFixture
    ) -> None:
        # given
        caplog.set_level(logging.INFO, logger="sqlalchemy.engine")
        async with DataR() as datar:
            for name in ("Batman", "Robin"):
                await records.create(Record(name=name), datar=datar)
            left = sql.SQLQuery(Record).where(where(Record.name, Eq("Batman")))
            right = sql.SQLQuery(Record)
            service = DataS(Record, read=RecordRead)
            caplog.clear()

            # when
            with caplog.at_level(logging.INFO, logger="sqlalchemy.engine"):
                rows = [
                    row
                    async for row in service.join(
                        left,
                        right,
                        on=(Record.score, Record.score),
                        datar=datar,
                    )
                ]

            # then
            assert "JOIN" in caplog.text
            assert {(a.name, b.name) for a, b in rows} == {
                ("Batman", "Batman"),
                ("Batman", "Robin"),
            }
            assert all(
                isinstance(left, ReadDTO) and type(right) is Record
                for left, right in rows
            )
            with pytest.raises(AttributeError):
                rows[0][0].__getattribute__("system_key")

            # then
            with pytest.raises(AttributeError, match="public"):
                _ = [
                    row
                    async for row in records.join(
                        left,
                        right,
                        on=(Record.system_key, Record.system_key),
                        datar=datar,
                    )
                ]

    async def test_lambda_join_falls_back_to_python(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        async with DataR() as datar:
            await records.create(Record(name="Batman"), datar=datar)
            left = sql.SQLQuery(Record).where(lambda row: row.name == "Batman")
            right = sql.SQLQuery(Record)

            # when
            rows = [
                row
                async for row in records.join(
                    left, right, on=(Record.score, Record.score), datar=datar
                )
            ]

            # then
            assert [(a.name, b.name) for a, b in rows] == [("Batman", "Batman")]

    async def test_join_is_lazy_and_closes_on_early_stop(
        self, records: DataS[Record]
    ) -> None:
        # given
        await records.create(Record(name="Batman"))
        calls: list[str] = []

        def check(operation: str) -> None:
            calls.append(operation)

        service = DataS(Record, dependencies=[Depends(check)])
        query = sql.SQLQuery(Record)
        rows = service.join(query, query, on=(Record.id, Record.id))
        assert calls == []
        assert dependency_resources.get() is None
        # when
        async with aclosing(rows):
            left, right = await anext(rows)
            assert left.id == right.id
        # then
        assert calls == ["join"]
        assert dependency_resources.get() is None
