from random import randint

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLPydField

from fastsprout.core import Field
from fastsprout.data.backend.sql import SoftDeletableSQLEntity, SQLQuery
from fastsprout.data.backend.sql.capabilities import (
    SQLCreatable,
    SQLDeletable,
    SQLFindable,
    SQLStreamable,
)


class Hero(SoftDeletableSQLEntity[int]):
    id: Field[int] = SQLPydField(
        default_factory=lambda: randint(-10000, 10000), primary_key=True
    )
    name: Field[str] = Field(default="")
    age: Field[int] = Field(default=0)


class HeroRepo(SQLCreatable, SQLDeletable, SQLFindable, SQLStreamable):
    @property
    def default_query(self) -> SQLQuery[Hero]:
        return SQLQuery(entity=Hero)


@pytest.fixture
async def repo():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Hero.metadata.create_all)
    setattr(  # noqa: B010 — pyright binds class callables as methods
        HeroRepo,
        "session_factory",
        async_sessionmaker(engine, expire_on_commit=False),
    )
    repo = HeroRepo()
    await repo.bulk_create([Hero(name=f"h{i}", age=i) for i in range(10)])
    yield repo
    await engine.dispose()


@pytest.fixture
def query() -> SQLQuery[Hero]:
    return SQLQuery(entity=Hero)


async def test_take_pushes_down_limit(repo, query) -> None:
    assert len(await repo.stream(query).take(3).to_list()) == 3


async def test_sort_by_field_pushes_down_order_by(repo, query) -> None:
    heroes = await repo.stream(query).sort(Hero.name, reverse=True).to_list()
    assert [h.name for h in heroes[:2]] == ["h9", "h8"]


async def test_count_pushes_down(repo, query) -> None:
    assert await repo.stream(query).count() == 10


async def test_first_pushes_down_limit(repo, query) -> None:
    first = await repo.stream(query).sort(Hero.age).first()
    assert first is not None
    assert first.age == 0


async def test_drop_pushes_down_offset(repo, query) -> None:
    heroes = await repo.stream(query).sort(Hero.age).drop(8).to_list()
    assert [h.age for h in heroes] == [8, 9]


async def test_value_stream_aggregates(repo, query) -> None:
    values = repo.stream(query).to_values(Hero.age)
    assert await values.sum() == sum(range(10))
    assert await values.count() == 10
    assert await values.sort().take(3).to_list() == [0, 1, 2]


async def test_python_predicate_falls_back(repo, query) -> None:
    evens = await (
        repo.stream(query)
        .sort(Hero.age)
        .filter(lambda h: h.age % 2 == 0)
        .to_list()
    )
    assert [h.age for h in evens] == [0, 2, 4, 6, 8]


async def test_chunked_streams_all_rows(repo, query) -> None:
    chunks = [c async for c in repo.stream(query).chunked(4)]
    assert [len(c) for c in chunks] == [4, 4, 2]


async def test_bulk_delete_commits_and_counts(repo, query) -> None:
    heroes = await repo.find_all(query)
    deleted = await repo.bulk_delete(heroes[:4])
    assert deleted == 4
    # fresh session: would see 10 again if the transaction rolled back
    assert len(await repo.find_all(query)) == 6


async def test_delete_by_query_commits(repo, query) -> None:
    assert await repo.delete_by_query(query) == 10
    assert await repo.find_all(query) == []


async def test_find_first_uses_limit(repo, query) -> None:
    first = await repo.find_first(query)
    assert first is not None
