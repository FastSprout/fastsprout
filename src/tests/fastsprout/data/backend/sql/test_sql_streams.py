import pytest
from sqlalchemy import Column, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data.backend.sql import SQLEntity, SQLQuery, SQLSignpost
from fastsprout.data.backend.sql.streams import SQLEntityStream
from fastsprout.testing.core import given, then, when

from .conftest import Hero


class NamedColumnEntity(SQLEntity[int, SQLSignpost]):
    id: ReadField[int] = SQLField(primary_key=True)
    display_name: Field[str] = SQLField(sa_column=Column("stored_name", String))


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
    async def test_take(self, entity_stream: SQLEntityStream[Hero]):
        # when
        found = await entity_stream.take(3).to_list()
        # then
        assert len(found) == 3

    async def test_sort_by_field(self, entity_stream: SQLEntityStream[Hero]):
        # when
        found = await entity_stream.sort(Hero.name, reverse=True).to_list()
        # then
        assert [hero.name for hero in found] == [
            f"h{i}" for i in reversed(range(10))
        ]

    async def test_count(self, entity_stream: SQLEntityStream[Hero]):
        # when
        count = await entity_stream.count()
        # then
        assert count == 10

    async def test_first(self, entity_stream: SQLEntityStream[Hero]):
        # when
        first = await entity_stream.sort(Hero.age).first()
        # then
        assert first is not None
        assert first.age == 0

    async def test_drop(self, entity_stream: SQLEntityStream[Hero]):
        # when
        found = await entity_stream.sort(Hero.age).drop(8).to_list()
        # then
        assert [hero.age for hero in found] == [8, 9]

    async def test_python_predicate(self, entity_stream: SQLEntityStream[Hero]):
        # when
        found = await (
            entity_stream.sort(Hero.age)
            .filter(lambda hero: hero.age % 2 == 0)
            .to_list()
        )
        # then
        assert [hero.age for hero in found] == [0, 2, 4, 6, 8]

    async def test_chunked(self, entity_stream: SQLEntityStream[Hero]):
        # when
        chunks = [chunk async for chunk in entity_stream.chunked(4)]
        # then
        assert [len(chunk) for chunk in chunks] == [4, 4, 2]
        assert sorted(hero.id for chunk in chunks for hero in chunk) == list(
            range(10)
        )


class TestSQLValueStream:
    async def test_sum(self, entity_stream: SQLEntityStream[Hero]):
        # given
        values = entity_stream.to_values(Hero.age)
        # when
        total = await values.sum()
        # then
        assert total == sum(range(10))

    async def test_count(self, entity_stream: SQLEntityStream[Hero]):
        # given
        values = entity_stream.to_values(Hero.age)
        # when
        count = await values.count()
        # then
        assert count == 10

    async def test_sort_and_take(self, entity_stream: SQLEntityStream[Hero]):
        # given
        values = entity_stream.to_values(Hero.age)
        # when
        found = await values.sort().take(3).to_list()
        # then
        assert found == [0, 1, 2]
