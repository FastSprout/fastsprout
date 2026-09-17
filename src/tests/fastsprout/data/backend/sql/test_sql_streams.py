from fastsprout.data.backend.sql.streams import SQLEntityStream

from .conftest import Hero


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
