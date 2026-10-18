import asyncio
from contextlib import aclosing

import pytest

from fastsprout.actions import DataS
from fastsprout.core import BaseSchema, Depends
from fastsprout.core.depends.scope import dependency_resources
from fastsprout.data import DataR, sql

from ...common import Record, RecordRead


class RecordSummary(BaseSchema):
    label: str


class TestMap:
    @pytest.mark.parametrize("asynchronous", [False, True])
    async def test_custom_mapping(
        self, records: DataS[Record], asynchronous: bool
    ) -> None:
        # given
        async with DataR() as datar:
            await records.create(Record(name="Batman"), datar=datar)
            query = sql.SQLQuery(Record).where(lambda row: row.name == "Batman")

            def summarize(row: Record) -> RecordSummary:
                return RecordSummary(label=row.name.upper())

            async def summarize_async(row: Record) -> RecordSummary:
                await asyncio.sleep(0)
                return summarize(row)

            # when
            summaries = [
                row
                async for row in records.map(
                    query,
                    summarize_async if asynchronous else summarize,
                    datar=datar,
                )
            ]

            # then
            assert summaries == [RecordSummary(label="BATMAN")]

    @pytest.mark.parametrize("fail", [False, True])
    async def test_mapping_is_lazy_and_closes_on_stop_or_failure(
        self, records: DataS[Record], fail: bool
    ) -> None:
        # given
        await records.create(Record(name="Batman"))
        calls: list[str] = []

        def check(operation: str) -> None:
            calls.append(operation)

        async def summarize(row: RecordRead) -> RecordSummary:
            assert isinstance(row, RecordRead)
            if fail:
                raise ValueError("mapping failed")
            return RecordSummary(label=row.name)

        service = DataS(Record, read=RecordRead, dependencies=[Depends(check)])
        rows = service.map(sql.SQLQuery(Record), summarize)
        assert calls == []
        assert dependency_resources.get() is None
        # when
        async with aclosing(rows):
            if fail:
                with pytest.raises(ValueError, match="mapping failed"):
                    await anext(rows)
            else:
                assert await anext(rows) == RecordSummary(label="Batman")
        # then
        assert calls == ["map"]
        assert dependency_resources.get() is None
