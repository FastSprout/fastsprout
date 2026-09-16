import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLPydField

from fastsprout.core import Field
from fastsprout.data.backend.sql.entity import (
    SQL_ENTITY_REGISTRY,
    SoftDeletableSQLEntity,
    SQLSignpost,
)
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.router import DataR


class Item(SoftDeletableSQLEntity[int]):
    id: Field[int | None] = SQLPydField(  # pyright: ignore[reportIncompatibleVariableOverride, reportAssignmentType]
        default=None, primary_key=True
    )
    name: Field[str] = Field(default="")


@pytest.fixture
async def signpost():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
    bound = SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))
    Item.__signpost__ = bound
    yield bound
    await engine.dispose()


async def test_reads_and_writes_in_one_context(signpost) -> None:
    async with DataR() as data:
        assert await data.stream(SQLQuery(entity=Item)).to_list() == []

        items = data.ability(Item)
        await items.bulk_create([Item(name="a"), Item(name="b")])

        # shared session: reads see uncommitted writes of this context
        rows = await data.stream(SQLQuery(entity=Item)).to_list()
        assert sorted(r.name for r in rows) == ["a", "b"]

    # finalized on clean exit
    async with DataR() as data:
        rows = await data.stream(SQLQuery(entity=Item)).to_list()
        assert sorted(r.name for r in rows) == ["a", "b"]


async def test_exception_aborts_everything(signpost) -> None:
    with pytest.raises(RuntimeError):
        async with DataR() as data:
            items = data.ability(Item)
            await items.bulk_create([Item(name="x")])
            raise RuntimeError("boom")

    async with DataR() as data:
        assert await data.stream(SQLQuery(entity=Item)).to_list() == []


async def test_explicit_abort_mid_context(signpost) -> None:
    async with DataR() as data:
        items = data.ability(Item)
        await items.bulk_create([Item(name="x")])
        await data.abort()

    async with DataR() as data:
        assert await data.stream(SQLQuery(entity=Item)).to_list() == []


async def test_repeated_stream_shares_session(signpost) -> None:
    async with DataR() as data:
        await data.stream(SQLQuery(entity=Item)).to_list()
        await data.stream(SQLQuery(entity=Item)).to_list()
    # one signpost registration, factory wrapped once — no errors
