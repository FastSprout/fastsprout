from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastsprout.actions import DataS
from fastsprout.core import inject_depends
from fastsprout.data import DataR, provide_datar, sql

from .common import Record


@pytest.fixture(autouse=True)
def datar_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        inject_depends.dependency_providers, DataR, provide_datar
    )


@pytest.fixture
async def records() -> AsyncIterator[DataS[Record]]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    Record.__signpost__ = sql.SQLSignpost(
        async_sessionmaker(engine, expire_on_commit=False)
    )
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Record.__table__.create)
        yield DataS(Record)
    finally:
        await engine.dispose()
