from collections.abc import Sequence

import pytest
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.capabilities import SQLAbilitable, SQLFindable
from fastsprout.data.capabilities.protocols import Findable
from fastsprout.testing.core import then, when

from .conftest import Hero


class TestSQLFindable:
    @when("the first row and all rows are requested for the selected query")
    async def found(
        self,
        capability: type[SQLFindable[Hero]],
        sql_signpost: SQLSignpost,
        selected_query: SQLQuery[Hero],
    ) -> tuple[Hero | None, Sequence[Hero]]:
        ability: Findable[Hero, SQLQuery[Hero]] = capability(sql_signpost)
        first = await ability.find_first(selected_query)
        found = await ability.find_all(selected_query)
        return first, found

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLFindable])
    @then("find operations preserve query ordering and pagination")
    def test_find_first(
        self, found: tuple[Hero | None, Sequence[Hero]]
    ) -> None:
        first, rows = found
        assert first is not None
        assert first.id == 6
        assert [hero.id for hero in rows] == [6, 7]

    @when("exactly one row is requested with a configured result limit")
    async def exactly_one(
        self,
        capability: type[SQLFindable[Hero]],
        sql_signpost: SQLSignpost,
        selected_query: SQLQuery[Hero],
        row_limit: int,
    ) -> Hero | MultipleResultsFound | NoResultFound:
        ability: Findable[Hero, SQLQuery[Hero]] = capability(sql_signpost)
        try:
            return await ability.find_exactly_one(
                selected_query.limit(row_limit)
            )
        except (MultipleResultsFound, NoResultFound) as error:
            return error

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLFindable])
    @pytest.mark.parametrize("row_limit", [0, 1, 2])
    @then("exactly-one distinguishes missing, unique and ambiguous results")
    def test_find_exactly_one(
        self,
        exactly_one: Hero | MultipleResultsFound | NoResultFound,
        row_limit: int,
    ) -> None:
        if row_limit == 0:
            assert isinstance(exactly_one, NoResultFound)
        elif row_limit == 2:
            assert isinstance(exactly_one, MultipleResultsFound)
        else:
            assert isinstance(exactly_one, Hero)
            assert exactly_one.id == 6

    @when("the first row of an empty query is requested")
    async def missing_first(
        self,
        capability: type[SQLFindable[Hero]],
        sql_signpost: SQLSignpost,
        selected_query: SQLQuery[Hero],
    ) -> Hero | None:
        ability: Findable[Hero, SQLQuery[Hero]] = capability(sql_signpost)
        return await ability.find_first(selected_query.limit(0))

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLFindable])
    @then("find-first returns None for an empty query")
    def test_find_first_missing(self, missing_first: Hero | None) -> None:
        assert missing_first is None
