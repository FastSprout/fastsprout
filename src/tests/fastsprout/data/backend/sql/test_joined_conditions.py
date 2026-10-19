import pytest

from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.capabilities.query import Expression, FieldPredicate
from fastsprout.testing.core import when_then

from .base_test_joined_query import (
    BaseTestSQLJoinedQuery,
    QueryCountry,
    QueryTeam,
)
from .conftest import Hero


class TestJoinedConditions(BaseTestSQLJoinedQuery):
    @when_then("runtime field checks reject an entity outside the join")
    def test_unjoined_field(
        self, joined_source: SQLSignpost, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        condition = Hero.id.eq(1)
        monkeypatch.setattr(condition, "source", QueryCountry)
        query = SQLQuery(Hero).join(QueryTeam, Hero.age == QueryTeam.id)
        query.where(condition)
        with pytest.raises(TypeError, match="joined entities"):
            query.build()

    @pytest.mark.parametrize("kind", ["native", "sync", "async"])
    @pytest.mark.parametrize("before_join", [False, True])
    @when_then(
        "field groups retain their owners across chained joins and pagination"
    )
    async def test_field_groups(
        self,
        selects: list[str],
        condition: Expression[Hero],
        kind: str,
        before_join: bool,
        consumed: list[int],
    ) -> None:
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
            stream = datar.stream(joined)
            assert selects == []
            assert consumed == []
            rows = await stream.to_list()
            assert [
                (hero.id, team.id, country.name) for hero, team, country in rows
            ] == [(4, 4, "Poland")]
            assert len(selects) == 1
            assert selects[0].count(" JOIN ") == 2
            assert consumed == ([] if kind == "native" else [3, 4])
