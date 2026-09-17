from typing import Any

from fastsprout.data.backend.sql import SQLQuery
from fastsprout.data.backend.sql.capabilities import SQLAbilitable

from .conftest import Hero


class TestSQLAbilitable:
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
