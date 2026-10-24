import pytest
from sqlalchemy.sql import Select

import fastsprout.data.router.implementation.datar as router
from fastsprout.core import Depends
from fastsprout.data import DataR, SimpleAsyncEntityStream
from fastsprout.data.backend.sql import SQLQuery
from fastsprout.data.backend.sql.capabilities import SQLAbilitable
from fastsprout.data.backend.sql.streams.entity_stream import SQLEntityStream
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.streams.protocols import AsyncEntityStreamable

from .conftest import JoinOrder


class IteratorAbility(SQLAbilitable[JoinOrder]):
    def stream(
        self, query: BaseQuery[JoinOrder, Select[tuple[JoinOrder]]], /
    ) -> AsyncEntityStreamable[JoinOrder]:
        return SimpleAsyncEntityStream(super().iter(query))


@pytest.mark.parametrize("projection", [False, True])
async def test_dependencies_guard_backend_streams_without_sql_stream_type(
    databases, monkeypatch: pytest.MonkeyPatch, projection: bool
) -> None:
    calls: list[str] = []

    def ability_of(entity: type[JoinOrder]) -> type[IteratorAbility]:
        assert entity is JoinOrder
        return IteratorAbility

    def reject(operation: str, query: SQLQuery[JoinOrder]) -> None:
        assert query.entity is JoinOrder
        calls.append(operation)
        raise PermissionError("Cannot read")

    monkeypatch.setattr(router, "ability_of", ability_of)
    async with DataR(dependencies=[Depends(reject)]) as data:
        source = data.ability(JoinOrder).stream(SQLQuery(entity=JoinOrder))
        assert isinstance(source, SimpleAsyncEntityStream)
        assert not isinstance(source, SQLEntityStream)
        assert calls == []
        with pytest.raises(PermissionError, match="Cannot read"):
            if projection:
                await source.to_values(JoinOrder.id).to_list()
            else:
                await source.to_list()
    assert calls == ["read"]


async def test_dependencies_preserve_sql_streams_and_recheck_each_read(
    databases,
) -> None:
    calls: list[str] = []

    def check(operation: str) -> None:
        calls.append(operation)

    async with DataR(dependencies=[Depends(check)]) as data:
        stream = data.stream(SQLQuery(entity=JoinOrder)).take(1)
        assert isinstance(stream, SQLEntityStream)
        assert calls == []
        assert len(await stream.to_list()) == 1
        assert await stream.count() == 1
    assert calls == ["read", "read"]
