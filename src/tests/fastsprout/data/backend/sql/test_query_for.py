from collections.abc import AsyncIterator

import pytest

from fastsprout.core import Undefined
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.capabilities import SQLAbilitable
from fastsprout.data.streams.protocols import AsyncEntityStreamable
from fastsprout.testing.core import given, then, when

from .conftest import Hero


class TestQueryFor:
    @given("an ability bound to Hero")
    def bound_ability(self, sql_signpost: SQLSignpost) -> SQLAbilitable[Hero]:
        return SQLAbilitable(sql_signpost, entity=Hero)

    @when("the bound ability constructs a query")
    def owner_query(
        self, bound_ability: SQLAbilitable[Hero], explicit: bool
    ) -> SQLQuery[Hero]:
        return bound_ability.query_for(Hero if explicit else Undefined)

    @then("the query preserves its owner and selects matching heroes")
    @pytest.mark.parametrize("explicit", [False, True])
    async def test_owner_query(
        self,
        bound_ability: SQLAbilitable[Hero],
        owner_query: SQLQuery[Hero],
    ) -> None:
        query = owner_query
        assert isinstance(query, SQLQuery)
        assert query.entity is Hero
        query.where(Hero.age.gte(8)).order_by(Hero.id)
        assert [hero.id async for hero in bound_ability.stream(query)] == [8, 9]

    @when("two queries are built and only the first is changed")
    def independent_queries(
        self, bound_ability: SQLAbilitable[Hero]
    ) -> tuple[SQLQuery[Hero], SQLQuery[Hero]]:
        first = bound_ability.query_for().where(Hero.age.gte(8))
        return first, bound_ability.query_for()

    @then("new queries do not share their conditions")
    def test_queries_are_independent(
        self, independent_queries: tuple[SQLQuery[Hero], SQLQuery[Hero]]
    ) -> None:
        first, second = independent_queries
        assert first is not second
        assert second.conditions == ()

    @when("an unbound ability is asked for explicit and implicit query owners")
    def unbound_queries(
        self, sql_ability: SQLAbilitable[Hero]
    ) -> tuple[SQLQuery[Hero], TypeError | None]:
        explicit = sql_ability.query_for(Hero)
        try:
            sql_ability.query_for()
        except TypeError as error:
            return explicit, error
        return explicit, None

    @then("query creation resolves or requires an owner")
    def test_unbound_requires_explicit_entity(
        self, unbound_queries: tuple[SQLQuery[Hero], TypeError | None]
    ) -> None:
        explicit, failure = unbound_queries
        assert explicit.entity is Hero
        assert isinstance(failure, TypeError)
        assert "unbound ability" in str(failure)

    @when("DataR constructs an ability and its query")
    async def routed_query(
        self, sql_signpost: SQLSignpost, monkeypatch: pytest.MonkeyPatch
    ) -> AsyncIterator[tuple[type[Hero], AsyncEntityStreamable[Hero]]]:
        monkeypatch.setattr(Hero, "__signpost__", sql_signpost, raising=False)
        async with DataR() as datar:
            ability = datar.ability(Hero)
            query = ability.query_for().where(Hero.age.gte(8)).order_by(Hero.id)
            yield query.entity, ability.stream(query)

    @then("the routed ability retains the entity owner")
    async def test_router_binds_owner(
        self, routed_query: tuple[type[Hero], AsyncEntityStreamable[Hero]]
    ) -> None:
        entity, stream = routed_query
        assert entity is Hero
        assert [hero.id async for hero in stream] == [8, 9]
