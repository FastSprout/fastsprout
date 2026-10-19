import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.core import Depends
from fastsprout.data import DataR
from fastsprout.data.backend.sql import (
    SQLJoinedQuery,
    SQLQuery,
    SQLSignpost,
)
from fastsprout.data.backend.sql.entity import SQLSource
from fastsprout.data.capabilities.query import Expression, FieldPredicate
from fastsprout.data.exceptions import NoSessionError
from fastsprout.testing.core import when_then

from .base_test_joined_query import (
    BaseTestSQLJoinedQuery,
    QueryCountry,
    QueryTeam,
)
from .conftest import Hero


class TestSQLJoinedQuery(BaseTestSQLJoinedQuery):
    @when_then("chained joins read all three entities with one lazy SQL query")
    async def test_chained_join(self, selects: list[str]) -> None:
        query = (
            SQLQuery(Hero)
            .join(QueryTeam, Hero.age == QueryTeam.id)
            .join(QueryCountry, QueryTeam.country_id == QueryCountry.id)
            .order_by(Hero.id)
        )
        async with DataR() as datar:
            stream = datar.stream(query)
            assert selects == []
            rows = await stream.to_list()
            assert [
                (hero.id, team.id, country.name) for hero, team, country in rows
            ] == [
                (3, 3, "Poland"),
                (4, 4, "Poland"),
            ]
            assert len(selects) == 1
            assert selects[0].count(" JOIN ") == 2

    @when_then("conditions and pagination apply to the joined result")
    @pytest.mark.parametrize("before_join", [False, True])
    async def test_query_options(
        self, selects: list[str], before_join: bool
    ) -> None:
        base = SQLQuery(Hero)
        if before_join:
            base.where(Hero.age.gte(3)).order_by(Hero.id).offset(1).limit(1)
        query = base.join(QueryTeam, Hero.age == QueryTeam.id)
        if not before_join:
            query.where(Hero.age.gte(3)).order_by(Hero.id).offset(1).limit(1)
        async with DataR() as datar:
            assert [
                (hero.id, team.id) async for hero, team in datar.stream(query)
            ] == [(4, 4)]
        assert len(selects) == 1

    @when_then(
        "joining retains the ordering used by cursors and later sort fields"
    )
    @pytest.mark.parametrize("cursor", [False, True])
    async def test_ordering_metadata(
        self, selects: list[str], sql_session: AsyncSession, cursor: bool
    ) -> None:
        first = await sql_session.get(Hero, 2)
        second = await sql_session.get(Hero, 1)
        assert first is not None and second is not None
        first.age, second.age = 3, 4
        await sql_session.flush()
        query = (
            SQLQuery(Hero)
            .where(Hero.id.in_([1, 2]))
            .order_by(Hero.age)
            .join(QueryTeam, Hero.age == QueryTeam.id)
            .join(QueryCountry, QueryTeam.country_id == QueryCountry.id)
        )
        assert query.orderings == (("age", False),)
        if cursor:
            query.after(first)
        else:
            query.order_by(Hero.id)
        assert query.orderings == (("age", False), ("id", False))
        async with DataR() as datar:
            assert [row[0].id async for row in datar.stream(query)] == (
                [1] if cursor else [2, 1]
            )

    @when_then(
        "joins evaluate fallback conditions lazily before paginating rows"
    )
    @pytest.mark.parametrize("before_join", [False, True])
    @pytest.mark.parametrize(
        "kind", ["sync", "async", "python", "async-python"]
    )
    async def test_fallback_conditions(
        self,
        selects: list[str],
        condition: Expression[Hero],
        consumed: list[int],
        before_join: bool,
        kind: str,
    ) -> None:
        base = SQLQuery(Hero)
        if before_join:
            base.where(condition)
        query = (
            base.join(QueryTeam, Hero.age == QueryTeam.id)
            .join(QueryCountry, QueryTeam.country_id == QueryCountry.id)
            .order_by(Hero.id)
            .offset(1)
            .limit(1)
        )
        if not before_join:
            query.where(condition)
        async with DataR() as datar:
            stream = datar.stream(query)
            assert consumed == []
            assert selects == []
            assert [row[0].id for row in await stream.to_list()] == [4]
            assert len(selects) == 1
            assert [row[0].id for row in await stream.to_list()] == [4]
            assert len(selects) == 2
            assert consumed == ([3, 4] if kind in {"sync", "async"} else [])

    @when_then(
        "joins reject different signpost instances and late reassignment"
    )
    @pytest.mark.parametrize("scoped", [False, True])
    def test_shared_source(
        self,
        joined_source: SQLSignpost,
        monkeypatch: pytest.MonkeyPatch,
        scoped: bool,
    ) -> None:
        query = SQLQuery(Hero, source=joined_source if scoped else None).join(
            QueryTeam, Hero.age == QueryTeam.id
        )
        monkeypatch.setattr(
            QueryTeam, "__signpost__", SQLSignpost(joined_source.factory)
        )
        with pytest.raises(TypeError, match="one shared signpost"):
            query.build()
        with pytest.raises(TypeError, match="one shared signpost"):
            SQLQuery(Hero).join(QueryTeam, Hero.age == QueryTeam.id)

    @when_then(
        "join fields must reference existing participants and the new entity"
    )
    def test_foreign_field(self, joined_source: SQLSignpost) -> None:
        with pytest.raises(TypeError, match="Join fields"):
            SQLQuery(Hero).join(QueryTeam, QueryCountry.id == QueryTeam.id)

    @when_then("joined streams cannot outlive their DataR context")
    async def test_closed_context(self, joined_source: SQLSignpost) -> None:
        query = SQLQuery(Hero).join(QueryTeam, Hero.age == QueryTeam.id)
        async with DataR() as datar:
            stream = datar.stream(query)
        with pytest.raises(NoSessionError):
            await stream.to_list()

    @when_then("DataR dependencies run lazily and can block the joined read")
    @pytest.mark.parametrize("allowed", [False, True])
    async def test_dependencies(
        self, selects: list[str], allowed: bool
    ) -> None:
        checked: list[type[Hero]] = []

        async def check(
            query: SQLJoinedQuery[
                SQLSource, FieldPredicate[QueryTeam], Hero, QueryTeam
            ],
        ) -> None:
            checked.append(query.entity)
            if not allowed:
                raise PermissionError("Denied")

        query = SQLQuery(Hero).join(QueryTeam, Hero.age == QueryTeam.id)
        async with DataR(dependencies=[Depends(check)]) as datar:
            stream = datar.stream(query)
            assert checked == []
            if allowed:
                assert len(await stream.to_list()) == 2
                assert len(selects) == 1
            else:
                with pytest.raises(PermissionError, match="Denied"):
                    await stream.to_list()
                assert selects == []
            assert checked == [Hero]
