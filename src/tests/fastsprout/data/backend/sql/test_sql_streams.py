import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.streams import SQLEntityStream, SQLValueStream
from fastsprout.data.streams.protocols import AsyncValueStreamable
from fastsprout.testing.core import given, then, when

from .conftest import Hero, NamedColumnEntity


class TestMappedFieldGetters:
    @given("a stream whose field and SQL column have different names")
    async def named_stream(
        self, sql_session: AsyncSession, sql_signpost: SQLSignpost
    ) -> SQLEntityStream[NamedColumnEntity]:
        sql_signpost.bind(NamedColumnEntity)
        await sql_session.run_sync(
            lambda session: NamedColumnEntity.__table__.create(
                session.connection()
            )
        )
        sql_session.add_all(
            NamedColumnEntity(id=index, display_name=name)
            for index, name in enumerate(("Ada", "Lin"), start=1)
        )
        await sql_session.flush()
        return SQLEntityStream(SQLQuery(NamedColumnEntity), sql_signpost)

    @when("a field getter sorts and projects a mapped stream")
    async def field_values(
        self, named_stream: SQLEntityStream[NamedColumnEntity], native: bool
    ) -> list[str]:
        stream = (
            named_stream
            if native
            else named_stream.filter(lambda row: row.id > 0)
        )
        return await (
            stream.sort(NamedColumnEntity.display_name, reverse=True)
            .to_values(NamedColumnEntity.display_name)
            .to_list()
        )

    @pytest.mark.parametrize("native", [False, True])
    @then("field getters sort and project in SQL and Python")
    def test_field_getters(self, field_values: list[str]) -> None:
        assert field_values == ["Lin", "Ada"]


class TestSQLEntityStream:
    @when(
        "native field predicates and Python field getters transform the stream"
    )
    async def transformed(
        self, entity_stream: SQLEntityStream[Hero]
    ) -> tuple[list[int], list[int], Hero | None]:
        selected = (
            await entity_stream.filter(Hero.age.gte(8))
            .distinct()
            .to_values(lambda hero: hero.age)
            .to_list()
        )
        reference: FieldRef[Hero, int, None] = FieldRef("age", Hero, None)
        fallback = (
            await entity_stream.sort(reference, reverse=True)
            .to_values(reference)
            .to_list()
        )
        empty = await entity_stream.take(0).first()
        return selected, fallback, empty

    @then(
        "pushdown and Python getters preserve values and empty-stream semantics"
    )
    def test_transformations(
        self, transformed: tuple[list[int], list[int], Hero | None]
    ) -> None:
        selected, fallback, empty = transformed
        assert selected == [8, 9]
        assert fallback == list(reversed(range(10)))
        assert empty is None

    @given("a query requiring Python filtering")
    def fallback(self, sql_signpost: SQLSignpost) -> SQLEntityStream[Hero]:
        return SQLEntityStream(
            SQLQuery(Hero).where(lambda hero: hero.age >= 0), sql_signpost
        )

    @when("fallback queries are sliced, deduplicated, sorted and projected")
    async def fallback_values(
        self, fallback: SQLEntityStream[Hero]
    ) -> tuple[list[int], list[int], int]:
        first = (
            await fallback.take(3).to_values(lambda hero: hero.age).to_list()
        )
        last = (
            await fallback.drop(8)
            .sort(lambda hero: -hero.age)
            .to_values(Hero.age)
            .to_list()
        )
        count = await fallback.distinct().count()
        return first, last, count

    @then("fallback operations preserve query conditions and stream order")
    def test_fallback_transformations(
        self, fallback_values: tuple[list[int], list[int], int]
    ) -> None:
        first, last, count = fallback_values
        assert first == [0, 1, 2]
        assert last == [9, 8]
        assert count == 10

    @when("the entity stream takes three rows")
    async def taken(self, entity_stream: SQLEntityStream[Hero]) -> list[Hero]:
        return await entity_stream.take(3).to_list()

    @then("take limits the result to three rows")
    def test_take(self, taken: list[Hero]) -> None:
        assert len(taken) == 3

    @when("the entity stream sorts names in reverse order")
    async def sorted_names(
        self, entity_stream: SQLEntityStream[Hero]
    ) -> list[str]:
        found = await entity_stream.sort(Hero.name, reverse=True).to_list()
        return [hero.name for hero in found]

    @then("field sorting preserves descending name order")
    def test_sort_by_field(self, sorted_names: list[str]) -> None:
        assert sorted_names == [f"h{i}" for i in reversed(range(10))]

    @when("the entity stream counts rows")
    async def count(self, entity_stream: SQLEntityStream[Hero]) -> int:
        return await entity_stream.count()

    @then("the stream contains ten entities")
    def test_count(self, count: int) -> None:
        assert count == 10

    @when("the youngest entity is requested")
    async def first(self, entity_stream: SQLEntityStream[Hero]) -> Hero | None:
        return await entity_stream.sort(Hero.age).first()

    @then("first returns the youngest entity")
    def test_first(self, first: Hero | None) -> None:
        assert first is not None
        assert first.age == 0

    @when("the first eight sorted entities are dropped")
    async def dropped(self, entity_stream: SQLEntityStream[Hero]) -> list[Hero]:
        return await entity_stream.sort(Hero.age).drop(8).to_list()

    @then("drop leaves the last two entities")
    def test_drop(self, dropped: list[Hero]) -> None:
        assert [hero.age for hero in dropped] == [8, 9]

    @when("a Python predicate selects even ages")
    async def filtered(
        self, entity_stream: SQLEntityStream[Hero]
    ) -> list[Hero]:
        return await (
            entity_stream.sort(Hero.age)
            .filter(lambda hero: hero.age % 2 == 0)
            .to_list()
        )

    @then("the fallback predicate retains matching entities in order")
    def test_python_predicate(self, filtered: list[Hero]) -> None:
        assert [hero.age for hero in filtered] == [0, 2, 4, 6, 8]

    @when("the entity stream is consumed in chunks of four")
    async def chunks(
        self, entity_stream: SQLEntityStream[Hero]
    ) -> list[list[Hero]]:
        return [chunk async for chunk in entity_stream.chunked(4)]

    @then("chunking yields every entity exactly once")
    def test_chunked(self, chunks: list[list[Hero]]) -> None:
        assert [len(chunk) for chunk in chunks] == [4, 4, 2]
        assert sorted(hero.id for chunk in chunks for hero in chunk) == list(
            range(10)
        )


class TestSQLValueStream:
    @given("a SQL stream projecting hero ages")
    def native(self, sql_signpost: SQLSignpost) -> SQLValueStream[int]:
        return SQLValueStream(select(Hero.age.orm), sql_signpost)

    @when("native and keyed terminals read the age stream")
    async def terminals(
        self, native: SQLValueStream[int]
    ) -> tuple[int | None, ...]:
        return (
            await native.first(),
            await native.take(0).first(),
            await native.min(),
            await native.max(),
            await native.min(lambda value: -value),
            await native.max(lambda value: -value),
        )

    @then("SQL aggregates and Python key functions retain their semantics")
    def test_terminals(self, terminals: tuple[int | None, ...]) -> None:
        assert terminals == (0, None, 0, 9, 9, 0)

    @when(
        "the SQL value stream drops, deduplicates and sorts using a Python key"
    )
    async def transformed(self, native: SQLValueStream[int]) -> list[int]:
        return (
            await native.drop(7).distinct().sort(lambda value: -value).to_list()
        )

    @then("value transformations preserve SQL pagination before keyed sorting")
    def test_transformations(self, transformed: list[int]) -> None:
        assert transformed == [9, 8, 7]

    @given("the ages projected from the entity stream")
    def values(
        self, entity_stream: SQLEntityStream[Hero]
    ) -> AsyncValueStreamable[int]:
        return entity_stream.to_values(Hero.age)

    @when("the value stream is summed")
    async def total(self, values: AsyncValueStreamable[int]) -> int | None:
        return await values.sum()

    @then("sum includes all projected ages")
    def test_sum(self, total: int | None) -> None:
        assert total == sum(range(10))

    @when("the projected values are counted")
    async def count(self, values: AsyncValueStreamable[int]) -> int:
        return await values.count()

    @then("projection preserves the number of rows")
    def test_count(self, count: int) -> None:
        assert count == 10

    @when("the three smallest values are requested")
    async def found(self, values: AsyncValueStreamable[int]) -> list[int]:
        return await values.sort().take(3).to_list()

    @then("sort and take return the first three ages")
    def test_sort_and_take(self, found: list[int]) -> None:
        assert found == [0, 1, 2]
