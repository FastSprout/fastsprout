from collections.abc import AsyncIterator
from contextlib import aclosing, nullcontext

import pytest

from fastsprout.actions import DataS
from fastsprout.core import Chunk, Depends, inject_depends
from fastsprout.core.depends.scope import dependency_resources
from fastsprout.data import DataR
from fastsprout.data.utils.iterable import resolve_any_iterable

from ...common import Record


@pytest.mark.parametrize("reject", [False, True])
async def test_chunks_share_provider_and_commit_or_roll_back_together(
    records: DataS[Record], monkeypatch: pytest.MonkeyPatch, reject: bool
) -> None:
    opened: list[DataR] = []
    checked: list[tuple[str, DataR]] = []

    async def provide() -> AsyncIterator[DataR]:
        async with DataR() as datar:
            opened.append(datar)
            yield datar

    async def check(entities: Chunk[Record], datar: DataR) -> None:
        async for entity in entities:
            checked.append((entity.name, datar))
            if reject and entity.name == "second":
                raise ValueError("Rejected second chunk")

    monkeypatch.setitem(inject_depends.dependency_providers, DataR, provide)
    service = DataS(Record, chunk_size=1, dependencies=[Depends(check)])
    stream = service.bulk_create(
        Record(name=name) for name in ("first", "second")
    )
    assert opened == []
    with (
        pytest.raises(ValueError, match="Rejected second chunk")
        if reject
        else nullcontext()
    ):
        await stream.to_list()

    assert len(opened) == 1
    assert checked == [("first", opened[0]), ("second", opened[0])]
    async with DataR() as datar:
        assert await records.count(datar=datar) == (0 if reject else 2)


class TestBulkStreamClosure:
    @pytest.mark.parametrize("operation", ["first", "any", "all", "callback"])
    async def test_partial_iteration_rolls_back_consumed_chunks(
        self, records: DataS[Record], operation: str
    ) -> None:
        # given
        stream = DataS(Record, chunk_size=1).bulk_create(
            Record(name=name) for name in ("first", "second")
        )

        def reject(entity: Record) -> None:
            raise ValueError(entity.name)

        # when
        if operation == "first":
            assert await stream.first() is not None
        elif operation == "any":
            assert await stream.any(lambda entity: entity.name == "first")
        elif operation == "all":
            assert not await stream.all(lambda entity: entity.name != "first")
        else:
            with pytest.raises(ValueError, match="first"):
                await stream.for_each(reject)

        # then
        assert dependency_resources.get() is None
        async with DataR() as datar:
            assert await records.count(datar=datar) == 0

    async def test_explicit_close_rolls_back_consumed_chunks(
        self, records: DataS[Record]
    ) -> None:
        # given
        stream = DataS(Record, chunk_size=1).bulk_create(
            Record(name=name) for name in ("first", "second")
        )
        # when
        async with aclosing(resolve_any_iterable(stream)) as items:
            assert (await anext(items)).name == "first"
        # then
        assert dependency_resources.get() is None
        async with DataR() as datar:
            assert await records.count(datar=datar) == 0
