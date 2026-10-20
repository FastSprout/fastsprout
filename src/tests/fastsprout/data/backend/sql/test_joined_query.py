from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.core import Depends
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLJoinedQuery, SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.entity import SQLSource
from fastsprout.data.capabilities.query import Expression, FieldPredicate
from fastsprout.data.exceptions import NoSessionError
from fastsprout.data.streams.protocols import AsyncJoinedStream
from fastsprout.testing.core import then, when

from .base_test_joined_query import (
    BaseTestSQLJoinedQuery,
    QueryCountry,
    QueryTeam,
)
from .conftest import Hero

type JoinedRows = AsyncJoinedStream[Hero, QueryTeam, QueryCountry]
type Orderings = tuple[tuple[str, bool], ...]


class TestSQLJoinedQuery(BaseTestSQLJoinedQuery):
    @when("a chained join is opened as a lazy stream")
    async def chained_stream(
        self, selects: list[str]
    ) -> AsyncIterator[JoinedRows]:
        query = (
            SQLQuery(Hero)
            .join(QueryTeam, Hero.age == QueryTeam.id)
            .join(QueryCountry, QueryTeam.country_id == QueryCountry.id)
            .order_by(Hero.id)
        )
        async with DataR() as datar:
            yield datar.stream(query)

    @then("chained joins read all three entities with one lazy SQL query")
    async def test_chained_join(
        self, selects: list[str], chained_stream: JoinedRows
    ) -> None:
        assert selects == []
        rows = await chained_stream.to_list()
        assert [
            (hero.id, team.id, country.name) for hero, team, country in rows
        ] == [(3, 3, "Poland"), (4, 4, "Poland")]
        assert len(selects) == 1
        assert selects[0].count(" JOIN ") == 2

    @when("conditions and pagination are configured before or after a join")
    async def option_stream(
        self, selects: list[str], before_join: bool
    ) -> AsyncIterator[AsyncJoinedStream[Hero, QueryTeam]]:
        base = SQLQuery(Hero)
        if before_join:
            base.where(Hero.age.gte(3)).order_by(Hero.id).offset(1).limit(1)
        query = base.join(QueryTeam, Hero.age == QueryTeam.id)
        if not before_join:
            query.where(Hero.age.gte(3)).order_by(Hero.id).offset(1).limit(1)
        async with DataR() as datar:
            yield datar.stream(query)

    @then("conditions and pagination apply to the joined result")
    @pytest.mark.parametrize("before_join", [False, True])
    async def test_query_options(
        self,
        selects: list[str],
        option_stream: AsyncJoinedStream[Hero, QueryTeam],
    ) -> None:
        assert [(hero.id, team.id) async for hero, team in option_stream] == [
            (4, 4)
        ]
        assert len(selects) == 1

    @when(
        "a previously sorted query is joined and its cursor or sort is extended"
    )
    async def ordered_stream(
        self, selects: list[str], sql_session: AsyncSession, cursor: bool
    ) -> AsyncIterator[tuple[Orderings, Orderings, JoinedRows]]:
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
        before = query.orderings
        if cursor:
            query.after(first)
        else:
            query.order_by(Hero.id)
        async with DataR() as datar:
            yield before, query.orderings, datar.stream(query)

    @then("joining retains the ordering used by cursors and later sort fields")
    @pytest.mark.parametrize("cursor", [False, True])
    async def test_ordering_metadata(
        self,
        ordered_stream: tuple[Orderings, Orderings, JoinedRows],
        cursor: bool,
    ) -> None:
        before, after, stream = ordered_stream
        assert before == (("age", False),)
        assert after == (("age", False), ("id", False))
        assert [row[0].id async for row in stream] == (
            [1] if cursor else [2, 1]
        )

    @when(
        "a joined stream is configured with fallback conditions and pagination"
    )
    async def fallback_stream(
        self, selects: list[str], condition: Expression[Hero], before_join: bool
    ) -> AsyncIterator[JoinedRows]:
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
            yield datar.stream(query)

    @then("joins evaluate fallback conditions lazily before paginating rows")
    @pytest.mark.parametrize("before_join", [False, True])
    @pytest.mark.parametrize(
        "kind", ["sync", "async", "python", "async-python"]
    )
    async def test_fallback_conditions(
        self,
        selects: list[str],
        consumed: list[int],
        kind: str,
        fallback_stream: JoinedRows,
    ) -> None:
        assert consumed == []
        assert selects == []
        assert [row[0].id for row in await fallback_stream.to_list()] == [4]
        assert len(selects) == 1
        assert [row[0].id for row in await fallback_stream.to_list()] == [4]
        assert len(selects) == 2
        assert consumed == ([3, 4] if kind in {"sync", "async"} else [])

    @when("a join participant is rebound to a different signpost instance")
    def reassigned_source(
        self,
        joined_source: SQLSignpost,
        monkeypatch: pytest.MonkeyPatch,
        scoped: bool,
    ) -> tuple[TypeError | None, TypeError | None]:
        query = SQLQuery(Hero, source=joined_source if scoped else None).join(
            QueryTeam, Hero.age == QueryTeam.id
        )
        monkeypatch.setattr(
            QueryTeam, "__signpost__", SQLSignpost(joined_source.factory)
        )
        build_error = join_error = None
        try:
            query.build()
        except TypeError as error:
            build_error = error
        try:
            SQLQuery(Hero).join(QueryTeam, Hero.age == QueryTeam.id)
        except TypeError as error:
            join_error = error
        return build_error, join_error

    @then("joins reject different signpost instances and late reassignment")
    @pytest.mark.parametrize("scoped", [False, True])
    def test_shared_source(
        self, reassigned_source: tuple[TypeError | None, TypeError | None]
    ) -> None:
        for failure in reassigned_source:
            assert isinstance(failure, TypeError)
            assert "one shared signpost" in str(failure)

    @when("join fields reference a non-participating entity")
    def foreign_join(self, joined_source: SQLSignpost) -> TypeError | None:
        try:
            SQLQuery(Hero).join(QueryTeam, QueryCountry.id == QueryTeam.id)
        except TypeError as error:
            return error
        return None

    @then("join fields must reference existing participants and the new entity")
    def test_foreign_field(self, foreign_join: TypeError | None) -> None:
        assert isinstance(foreign_join, TypeError)
        assert "Join fields" in str(foreign_join)

    @when("the DataR context is closed before its joined stream is consumed")
    async def closed_stream(
        self, joined_source: SQLSignpost
    ) -> AsyncJoinedStream[Hero, QueryTeam]:
        query = SQLQuery(Hero).join(QueryTeam, Hero.age == QueryTeam.id)
        async with DataR() as datar:
            stream = datar.stream(query)
        return stream

    @then("joined streams cannot outlive their DataR context")
    async def test_closed_context(
        self, closed_stream: AsyncJoinedStream[Hero, QueryTeam]
    ) -> None:
        with pytest.raises(NoSessionError):
            await closed_stream.to_list()

    @when("a joined stream is opened with a permitting or rejecting dependency")
    async def guarded_stream(
        self, selects: list[str], allowed: bool
    ) -> AsyncIterator[
        tuple[AsyncJoinedStream[Hero, QueryTeam], list[type[Hero]]]
    ]:
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
            yield datar.stream(query), checked

    @then("DataR dependencies run lazily and can block the joined read")
    @pytest.mark.parametrize("allowed", [False, True])
    async def test_dependencies(
        self,
        selects: list[str],
        allowed: bool,
        guarded_stream: tuple[
            AsyncJoinedStream[Hero, QueryTeam], list[type[Hero]]
        ],
    ) -> None:
        stream, checked = guarded_stream
        assert checked == []
        if allowed:
            assert len(await stream.to_list()) == 2
            assert len(selects) == 1
        else:
            with pytest.raises(PermissionError, match="Denied"):
                await stream.to_list()
            assert selects == []
        assert checked == [Hero]
