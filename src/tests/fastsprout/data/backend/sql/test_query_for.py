import pytest

from fastsprout.core import Undefined
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.capabilities import SQLAbilitable
from fastsprout.testing.core import given, then, when_then

from .conftest import Hero


class TestQueryFor:
    @given("an ability bound to Hero")
    def bound_ability(self, sql_signpost: SQLSignpost) -> SQLAbilitable[Hero]:
        return SQLAbilitable(sql_signpost, entity=Hero)

    @then("the query preserves its owner and selects matching heroes")
    @pytest.mark.parametrize("explicit", [False, True])
    async def test_owner_query(
        self, bound_ability: SQLAbilitable[Hero], explicit: bool
    ) -> None:
        query = bound_ability.query_for(Hero if explicit else Undefined)
        assert isinstance(query, SQLQuery)
        assert query.entity is Hero
        query.where(Hero.age.gte(8)).order_by(Hero.id)
        assert [hero.id async for hero in bound_ability.stream(query)] == [8, 9]

    @then("the query preserves its owner and selects matching heroes")
    def test_queries_are_independent(
        self, bound_ability: SQLAbilitable[Hero]
    ) -> None:
        first = bound_ability.query_for().where(Hero.age.gte(8))
        second = bound_ability.query_for()
        assert first is not second
        assert second.conditions == ()

    @when_then("query creation resolves or requires an owner")
    def test_unbound_requires_explicit_entity(
        self, sql_ability: SQLAbilitable[Hero]
    ) -> None:
        assert sql_ability.query_for(Hero).entity is Hero
        with pytest.raises(TypeError, match="unbound ability"):
            sql_ability.query_for()

    @when_then("query creation resolves or requires an owner")
    async def test_router_binds_owner(
        self, sql_signpost: SQLSignpost, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(Hero, "__signpost__", sql_signpost, raising=False)
        async with DataR() as datar:
            ability = datar.ability(Hero)
            query = ability.query_for().where(Hero.age.gte(8)).order_by(Hero.id)
            assert query.entity is Hero
            assert [hero.id async for hero in ability.stream(query)] == [8, 9]
