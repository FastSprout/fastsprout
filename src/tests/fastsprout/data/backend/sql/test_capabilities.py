from collections.abc import Callable, Sequence

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.capabilities import (
    SQLAbilitable,
    SQLDeletable,
    SQLIterable,
)
from fastsprout.data.backend.sql.capabilities.updatable import (
    SQLUpdatable,
    SQLUpdatableByQuery,
)
from fastsprout.data.capabilities.protocols import (
    Deletable,
    Iterable,
    UpdatableByQuery,
)
from fastsprout.data.capabilities.query import Expression, FieldPredicate
from fastsprout.data.streams.implementation import (
    SimpleAsyncEntityStream,
    SimpleAsyncValueStream,
)
from fastsprout.data.types import PredicateCallable
from fastsprout.testing.core import given, then, when

from .conftest import Hero


class TestSQLAbilitable:
    @given("a query combining a lower bound and a native or Python upper bound")
    def logical_query(
        self,
        operation: Callable[
            [FieldPredicate[Hero], PredicateCallable[Hero]], Expression[Hero]
        ],
        python_predicate: bool,
    ) -> SQLQuery[Hero]:
        upper: PredicateCallable[Hero] = (
            (lambda hero: hero.age <= 7)
            if python_predicate
            else Hero.age.lte(7)
        )
        return (
            SQLQuery(Hero)
            .where(operation(Hero.age.gte(5), upper))
            .order_by(Hero.id)
        )

    @when("the logical query is consumed")
    async def logical_ids(
        self, sql_ability: SQLAbilitable[Hero], logical_query: SQLQuery[Hero]
    ) -> list[int]:
        return [hero.id async for hero in sql_ability.stream(logical_query)]

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
    @then("native and fallback predicates retain the same logical semantics")
    def test_query_logical_operations(
        self, logical_ids: list[int], expected: list[int]
    ) -> None:
        assert logical_ids == expected

    @given("a membership predicate backed by a list or one-shot iterator")
    def membership(self, source_kind: str) -> FieldPredicate[Hero]:
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
        return Hero.age.in_(source)

    @when(
        "the membership predicate is consumed twice in SQL and once in Python"
    )
    async def membership_results(
        self,
        sql_ability: SQLAbilitable[Hero],
        membership: FieldPredicate[Hero],
    ) -> tuple[list[Hero], list[Hero], list[Hero]]:
        query = SQLQuery(Hero).where(membership).order_by(Hero.id)
        first = await sql_ability.stream(query).to_list()
        repeated = await sql_ability.stream(query).to_list()
        in_memory = (
            await SimpleAsyncEntityStream(first).filter(membership).to_list()
        )
        return first, repeated, in_memory

    @pytest.mark.parametrize(
        "source_kind", ["list", "iterator", "async_iterator"]
    )
    @then("membership sources remain reusable across SQL and Python")
    def test_reusable_membership(
        self, membership_results: tuple[list[Hero], list[Hero], list[Hero]]
    ) -> None:
        first, repeated, in_memory = membership_results
        assert [hero.id for hero in first] == [2, 7]
        assert repeated == first == in_memory

    @when("a query combines three overlapping predicates with XOR")
    async def xor_ids(self, sql_ability: SQLAbilitable[Hero]) -> list[int]:
        query = SQLQuery(Hero)
        query.where(
            query.Xor(Hero.age.gte(2), Hero.age.gte(4), Hero.age.gte(6))
        ).order_by(Hero.id)
        found = await sql_ability.stream(query).to_list()
        return [hero.id for hero in found]

    @then("XOR retains rows matching an odd number of predicates")
    def test_xor_keeps_three_matches(self, xor_ids: list[int]) -> None:
        assert xor_ids == [2, 3, 6, 7, 8, 9]

    @when("selected entities are bulk-updated from sync or async input")
    async def bulk_updated(
        self,
        sql_ability: SQLUpdatable[Hero],
        sql_session: AsyncSession,
        async_source: bool,
    ) -> tuple[Sequence[Hero], Hero | None, Hero | None, Sequence[Hero]]:
        entities = [
            Hero(id=key, name=f"updated-{key}", age=20) for key in (7, 2)
        ]

        source = SimpleAsyncEntityStream(entities) if async_source else entities
        updated = await sql_ability.bulk_update(source)

        sql_session.expire_all()
        stored = await sql_session.get(Hero, 7)
        untouched = await sql_session.get(Hero, 3)
        empty = await sql_ability.bulk_update([])
        return updated, stored, untouched, empty

    @pytest.mark.parametrize("async_source", [False, True])
    @then("bulk update changes only its inputs and accepts an empty batch")
    def test_bulk_update(
        self,
        bulk_updated: tuple[
            Sequence[Hero], Hero | None, Hero | None, Sequence[Hero]
        ],
    ) -> None:
        updated, stored, untouched, empty = bulk_updated
        assert sorted((hero.id, hero.name, hero.age) for hero in updated) == [
            (2, "updated-2", 20),
            (7, "updated-7", 20),
        ]
        assert stored is not None and stored.name == "updated-7"
        assert untouched is not None and untouched.name == "h3"

        assert empty == []

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

    @when("a selected query is deleted")
    async def deleted_by_query(
        self,
        capability: type[SQLDeletable[Hero]],
        sql_signpost: SQLSignpost,
        selected_query: SQLQuery[Hero],
    ) -> int:
        ability: Deletable[Hero, SQLQuery[Hero]] = capability(sql_signpost)
        return await ability.delete_by_query(selected_query)

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLDeletable])
    @then("query deletion removes only the selected rows")
    async def test_delete_by_query(
        self, deleted_by_query: int, sql_session: AsyncSession
    ) -> None:
        assert deleted_by_query == 2
        assert await sql_session.get(Hero, 6) is None
        assert await sql_session.get(Hero, 7) is None
        assert await sql_session.get(Hero, 5) is not None
        assert await sql_session.get(Hero, 8) is not None

    @when("the selected rows are iterated individually and in chunks")
    async def iterated(
        self,
        capability: type[SQLIterable[Hero]],
        sql_signpost: SQLSignpost,
        selected_query: SQLQuery[Hero],
    ) -> tuple[list[int], list[list[int]]]:
        ability: Iterable[Hero, SQLQuery[Hero]] = capability(sql_signpost)
        found = [hero.id async for hero in ability.iter(selected_query)]
        chunks = [
            [hero.id for hero in chunk]
            async for chunk in ability.iter_per(selected_query, chunk_size=1)
        ]
        return found, chunks

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLIterable])
    @then("iteration and chunking preserve the selected row order")
    def test_iter(self, iterated: tuple[list[int], list[list[int]]]) -> None:
        found, chunks = iterated
        assert found == [6, 7]
        assert chunks == [[6], [7]]

    @when("the selected rows receive a field assignment")
    async def updated_by_query(
        self,
        capability: type[SQLUpdatableByQuery[Hero]],
        sql_signpost: SQLSignpost,
        selected_query: SQLQuery[Hero],
    ) -> int:
        ability: UpdatableByQuery[Hero, SQLQuery[Hero]] = capability(
            sql_signpost
        )
        return await ability.update_by_query(
            selected_query, Hero.name.set("updated")
        )

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLUpdatableByQuery])
    @then("query updates preserve every non-selected row")
    async def test_update_by_query(
        self, updated_by_query: int, sql_session: AsyncSession
    ) -> None:
        assert updated_by_query == 2
        sql_session.expire_all()
        for key in range(10):
            hero = await sql_session.get(Hero, key)
            assert hero is not None
            assert hero.name == ("updated" if key in (6, 7) else f"h{key}")
