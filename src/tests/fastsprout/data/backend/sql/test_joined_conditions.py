from collections.abc import AsyncIterator

import pytest

from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.capabilities.query import Expression, FieldPredicate
from fastsprout.data.streams.protocols import AsyncJoinedStream
from fastsprout.testing.core import then, when

from .base_test_joined_query import (
    BaseTestSQLJoinedQuery,
    QueryCountry,
    QueryTeam,
)
from .conftest import Hero


class TestJoinedConditions(BaseTestSQLJoinedQuery):
    @when("a condition is changed to reference an entity outside the join")
    def foreign_condition(
        self, joined_source: SQLSignpost, monkeypatch: pytest.MonkeyPatch
    ) -> TypeError | None:
        condition = Hero.id.eq(1)
        monkeypatch.setattr(condition, "source", QueryCountry)
        query = SQLQuery(Hero).join(QueryTeam, Hero.age == QueryTeam.id)
        query.where(condition)
        try:
            query.build()
        except TypeError as error:
            return error
        return None

    @then("runtime field checks reject an entity outside the join")
    def test_unjoined_field(self, foreign_condition: TypeError | None) -> None:
        assert isinstance(foreign_condition, TypeError)
        assert "joined entities" in str(foreign_condition)

    @when("a field group is attached before or after another join")
    async def grouped_stream(
        self,
        selects: list[str],
        condition: Expression[Hero],
        before_join: bool,
    ) -> AsyncIterator[AsyncJoinedStream[Hero, QueryTeam, QueryCountry]]:
        assert isinstance(condition, FieldPredicate)
        query = SQLQuery(Hero).join(QueryTeam, Hero.age == QueryTeam.id)
        group = query.Or(
            Hero.id.eq(999),
            FieldPredicate(QueryTeam, "id", condition.condition),
        )
        if before_join:
            query.where(group)
        joined = query.join(
            QueryCountry, QueryTeam.country_id == QueryCountry.id
        )
        if not before_join:
            joined.where(group)
        joined.where(QueryCountry.name.eq("Poland"), QueryTeam.country_id.eq(1))
        joined.order_by(Hero.id).offset(1).limit(1)
        async with DataR() as datar:
            yield datar.stream(joined)

    @pytest.mark.parametrize("kind", ["native", "sync", "async"])
    @pytest.mark.parametrize("before_join", [False, True])
    @then(
        "field groups retain their owners across chained joins and pagination"
    )
    async def test_field_groups(
        self,
        selects: list[str],
        consumed: list[int],
        kind: str,
        grouped_stream: AsyncJoinedStream[Hero, QueryTeam, QueryCountry],
    ) -> None:
        assert selects == []
        assert consumed == []
        rows = await grouped_stream.to_list()
        assert [
            (hero.id, team.id, country.name) for hero, team, country in rows
        ] == [(4, 4, "Poland")]
        assert len(selects) == 1
        assert selects[0].count(" JOIN ") == 2
        assert consumed == ([] if kind == "native" else [3, 4])
