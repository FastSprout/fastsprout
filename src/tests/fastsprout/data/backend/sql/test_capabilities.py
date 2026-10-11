from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.sql import SQLQuery
from fastsprout.data.backend.sql.capabilities import SQLAbilitable
from fastsprout.data.backend.sql.capabilities.updatable import SQLUpdatable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream

from .conftest import Hero


class TestSQLAbilitable:
    @pytest.mark.parametrize("async_source", [False, True])
    async def test_bulk_update(
        self,
        sql_ability: SQLUpdatable[Hero],
        sql_session: AsyncSession,
        async_source: bool,
    ) -> None:
        entities = [
            Hero(id=key, name=f"updated-{key}", age=20) for key in (7, 2)
        ]

        source = SimpleAsyncEntityStream(entities) if async_source else entities
        updated = await sql_ability.bulk_update(source)

        assert sorted((hero.id, hero.name, hero.age) for hero in updated) == [
            (2, "updated-2", 20),
            (7, "updated-7", 20),
        ]
        sql_session.expire_all()
        stored = await sql_session.get(Hero, 7)
        untouched = await sql_session.get(Hero, 3)
        assert stored is not None and stored.name == "updated-7"
        assert untouched is not None and untouched.name == "h3"

        assert await sql_ability.bulk_update([]) == []

    async def test_bulk_delete(
        self,
        sql_ability: SQLAbilitable[Hero, SQLQuery[Any]],
        query: SQLQuery[Hero],
    ):
        # given
        found = await sql_ability.stream(query).sort(Hero.id).to_list()
        # when
        deleted = await sql_ability.bulk_delete(found[:4])
        remaining = await sql_ability.stream(query).sort(Hero.id).to_list()
        # then
        assert deleted == 4
        assert [hero.id for hero in remaining] == list(range(4, 10))

    async def test_delete_by_query(
        self,
        sql_ability: SQLAbilitable[Hero, SQLQuery[Any]],
        query: SQLQuery[Hero],
    ):
        # when
        deleted = await sql_ability.delete_by_query(query)
        # then
        assert deleted == 10
        assert await sql_ability.stream(query).to_list() == []

    async def test_find_first(
        self,
        sql_ability: SQLAbilitable[Hero, SQLQuery[Any]],
        query: SQLQuery[Hero],
    ):
        # when
        first = await sql_ability.find_first(query)
        # then
        assert first is not None
        assert first.id in range(10)
