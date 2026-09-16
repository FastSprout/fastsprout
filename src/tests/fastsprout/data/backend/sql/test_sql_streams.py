from random import randint

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLPydField

from fastsprout.core import Field
from fastsprout.data.backend.sql import (
    SoftDeletableSQLEntity,
    SQLQuery,
)
from fastsprout.data.backend.sql.entity import SQLSignpost
from fastsprout.data.router import DataR


class Hero(SoftDeletableSQLEntity[int]):
    id: Field[int] = SQLPydField(  # pyright: ignore[reportAssignmentType]
        default_factory=lambda: randint(-10000, 10000), primary_key=True
    )
    name: Field[str] = Field(default="")
    age: Field[int] = Field(default=0)


@pytest.fixture
async def ctx():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Hero.metadata.create_all)
    Hero.__signpost__ = SQLSignpost(
        async_sessionmaker(engine, expire_on_commit=False)
    )
    async with DataR() as data:
        heroes = data.ability(Hero)
        await heroes.bulk_create([Hero(name=f"h{i}", age=i) for i in range(10)])
        yield data, heroes
    await engine.dispose()


@pytest.fixture
def query() -> SQLQuery[Hero]:
    return SQLQuery(entity=Hero)


async def test_take_pushes_down_limit(ctx, query) -> None:
    _, heroes = ctx
    assert len(await heroes.stream(query).take(3).to_list()) == 3


async def test_sort_by_field_pushes_down_order_by(ctx, query) -> None:
    _, heroes = ctx
    found = await heroes.stream(query).sort(Hero.name, reverse=True).to_list()
    assert [h.name for h in found[:2]] == ["h9", "h8"]


async def test_count_pushes_down(ctx, query) -> None:
    _, heroes = ctx
    assert await heroes.stream(query).count() == 10


async def test_first_pushes_down_limit(ctx, query) -> None:
    _, heroes = ctx
    first = await heroes.stream(query).sort(Hero.age).first()
    assert first is not None
    assert first.age == 0


async def test_drop_pushes_down_offset(ctx, query) -> None:
    _, heroes = ctx
    found = await heroes.stream(query).sort(Hero.age).drop(8).to_list()
    assert [h.age for h in found] == [8, 9]


async def test_value_stream_aggregates(ctx, query) -> None:
    _, heroes = ctx
    values = heroes.stream(query).to_values(Hero.age)
    assert await values.sum() == sum(range(10))
    assert await values.count() == 10
    assert await values.sort().take(3).to_list() == [0, 1, 2]


async def test_python_predicate_falls_back(ctx, query) -> None:
    _, heroes = ctx
    evens = await (
        heroes.stream(query)
        .sort(Hero.age)
        .filter(lambda h: h.age % 2 == 0)
        .to_list()
    )
    assert [h.age for h in evens] == [0, 2, 4, 6, 8]


async def test_chunked_streams_all_rows(ctx, query) -> None:
    _, heroes = ctx
    chunks = [c async for c in heroes.stream(query).chunked(4)]
    assert [len(c) for c in chunks] == [4, 4, 2]


async def test_bulk_delete_visible_in_context(ctx, query) -> None:
    _, heroes = ctx
    found = await heroes.stream(query).to_list()
    deleted = await heroes.bulk_delete(found[:4])
    assert deleted == 4
    assert len(await heroes.stream(query).to_list()) == 6


async def test_delete_by_query(ctx, query) -> None:
    _, heroes = ctx
    assert await heroes.delete_by_query(query) == 10
    assert await heroes.stream(query).to_list() == []


async def test_find_first(ctx, query) -> None:
    _, heroes = ctx
    first = await heroes.find_first(query)
    assert first is not None
