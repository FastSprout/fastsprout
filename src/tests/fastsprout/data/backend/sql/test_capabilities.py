from collections.abc import Callable

import pytest
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.capabilities import (
    SQLAbilitable,
    SQLDeletable,
    SQLFindable,
    SQLIterable,
)
from fastsprout.data.backend.sql.capabilities.updatable import (
    SQLUpdatable,
    SQLUpdatableByQuery,
)
from fastsprout.data.capabilities.protocols import (
    Deletable,
    Findable,
    Iterable,
    UpdatableByQuery,
)
from fastsprout.data.capabilities.query import Expression, FieldPredicate
from fastsprout.data.streams.implementation import (
    SimpleAsyncEntityStream,
    SimpleAsyncValueStream,
)
from fastsprout.data.types import PredicateCallable
from fastsprout.testing.core import then, when

from .conftest import Hero


class TestSQLAbilitable:
    @pytest.mark.parametrize(
        "operation, expected",
        [
            (SQLQuery.And, [5, 6, 7]),
            (SQLQuery.Or, list(range(10))),
            (SQLQuery.Xor, [0, 1, 2, 3, 4, 8, 9]),
            (SQLQuery.Nand, [0, 1, 2, 3, 4, 8, 9]),
        ],
    )
    @pytest.mark.parametrize("python_predicate", [False, True])
    async def test_query_logical_operations(
        self,
        sql_ability: SQLAbilitable[Hero],
        operation: Callable[
            [FieldPredicate[Hero], PredicateCallable[Hero]], Expression[Hero]
        ],
        expected: list[int],
        python_predicate: bool,
    ) -> None:
        # given
        query = SQLQuery(Hero)
        upper: PredicateCallable[Hero] = (
            (lambda hero: hero.age <= 7)
            if python_predicate
            else Hero.age.lte(7)
        )
        query.where(operation(Hero.age.gte(5), upper)).order_by(Hero.id)
        # when
        found = await sql_ability.stream(query).to_list()
        # then
        assert [hero.id for hero in found] == expected

    @pytest.mark.parametrize(
        "source_kind", ["list", "iterator", "async_iterator"]
    )
    async def test_reusable_membership(
        self,
        sql_ability: SQLAbilitable[Hero],
        source_kind: str,
    ) -> None:
        # given
        values = [2, 7]
        source = (
            iter(values)
            if source_kind == "iterator"
            else (
                aiter(SimpleAsyncValueStream(values))
                if source_kind == "async_iterator"
                else values
            )
        )
        predicate = Hero.age.in_(source)
        query = SQLQuery(Hero).where(predicate).order_by(Hero.id)
        # when
        first = await sql_ability.stream(query).to_list()
        repeated = await sql_ability.stream(query).to_list()
        in_memory = (
            await SimpleAsyncEntityStream(first).filter(predicate).to_list()
        )
        # then
        assert [hero.id for hero in first] == [2, 7]
        assert repeated == first == in_memory

    async def test_xor_keeps_three_matches(
        self, sql_ability: SQLAbilitable[Hero]
    ) -> None:
        # given
        query = SQLQuery(Hero)
        query.where(
            query.Xor(Hero.age.gte(2), Hero.age.gte(4), Hero.age.gte(6))
        ).order_by(Hero.id)
        # when
        found = await sql_ability.stream(query).to_list()
        # then
        assert [hero.id for hero in found] == [2, 3, 6, 7, 8, 9]

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

    @when("an ability updates a missing entity")
    async def missing_update(
        self,
        capability: type[SQLUpdatable[Hero]],
        sql_signpost: SQLSignpost,
    ) -> LookupError | None:
        ability = capability(sql_signpost)
        try:
            await ability.update(Hero(id=100, name="Missing"))
        except LookupError as error:
            return error
        return None

    @then("updating a missing entity never inserts it")
    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLUpdatable])
    async def test_update_missing_entity_does_not_insert(
        self,
        missing_update: LookupError | None,
        sql_session: AsyncSession,
    ) -> None:
        assert isinstance(missing_update, LookupError)
        assert "No Hero" in str(missing_update)
        assert await sql_session.get(Hero, 100) is None

    @when("the first four selected entities are bulk-deleted")
    async def deleted_count(
        self,
        sql_ability: SQLAbilitable[Hero],
        query: SQLQuery[Hero],
    ) -> int:
        query.order_by(Hero.id)
        found = await sql_ability.stream(query).to_list()
        return await sql_ability.bulk_delete(found[:4])

    @then("bulk deletion removes only the selected entities")
    async def test_bulk_delete(
        self,
        sql_ability: SQLAbilitable[Hero],
        query: SQLQuery[Hero],
        deleted_count: int,
    ) -> None:
        remaining = await sql_ability.stream(query).to_list()
        assert deleted_count == 4
        assert [hero.id for hero in remaining] == list(range(4, 10))

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLDeletable])
    async def test_delete_by_query(
        self,
        capability: type[SQLDeletable[Hero]],
        sql_signpost: SQLSignpost,
        sql_session: AsyncSession,
        selected_query: SQLQuery[Hero],
    ) -> None:
        # given
        ability: Deletable[Hero, SQLQuery[Hero]] = capability(sql_signpost)
        # when
        deleted = await ability.delete_by_query(selected_query)
        # then
        assert deleted == 2
        assert await sql_session.get(Hero, 6) is None
        assert await sql_session.get(Hero, 7) is None
        assert await sql_session.get(Hero, 5) is not None
        assert await sql_session.get(Hero, 8) is not None

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLFindable])
    async def test_find_first(
        self,
        capability: type[SQLFindable[Hero]],
        sql_signpost: SQLSignpost,
        selected_query: SQLQuery[Hero],
    ) -> None:
        # given
        ability: Findable[Hero, SQLQuery[Hero]] = capability(sql_signpost)
        # when
        first = await ability.find_first(selected_query)
        found = await ability.find_all(selected_query)
        # then
        assert first is not None
        assert first.id == 6
        assert [hero.id for hero in found] == [6, 7]
        # then
        with pytest.raises(MultipleResultsFound):
            await ability.find_exactly_one(selected_query)
        selected_query.limit(1)
        assert (await ability.find_exactly_one(selected_query)).id == 6
        selected_query.limit(0)
        assert await ability.find_first(selected_query) is None
        with pytest.raises(NoResultFound):
            await ability.find_exactly_one(selected_query)

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLIterable])
    async def test_iter(
        self,
        capability: type[SQLIterable[Hero]],
        sql_signpost: SQLSignpost,
        selected_query: SQLQuery[Hero],
    ) -> None:
        # given
        ability: Iterable[Hero, SQLQuery[Hero]] = capability(sql_signpost)
        # when
        found = [hero.id async for hero in ability.iter(selected_query)]
        chunks = [
            [hero.id for hero in chunk]
            async for chunk in ability.iter_per(selected_query, chunk_size=1)
        ]
        # then
        assert found == [6, 7]
        assert chunks == [[6], [7]]

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLUpdatableByQuery])
    async def test_update_by_query(
        self,
        capability: type[SQLUpdatableByQuery[Hero]],
        sql_signpost: SQLSignpost,
        sql_session: AsyncSession,
        selected_query: SQLQuery[Hero],
    ) -> None:
        # given
        ability: UpdatableByQuery[Hero, SQLQuery[Hero]] = capability(
            sql_signpost
        )
        # when
        updated = await ability.update_by_query(
            selected_query, Hero.name.set("updated")
        )
        # then
        assert updated == 2
        sql_session.expire_all()
        for key in range(10):
            hero = await sql_session.get(Hero, key)
            assert hero is not None
            assert hero.name == ("updated" if key in (6, 7) else f"h{key}")
