from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from fastsprout.actions import DataS
from fastsprout.core import inject_depends
from fastsprout.data import DataR, provide_datar, sql

from .common import League, Record, Team, TeamRecord


@pytest.fixture(autouse=True)
def datar_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        inject_depends.dependency_providers, DataR, provide_datar
    )


@pytest.fixture
async def sql_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def records(sql_engine: AsyncEngine) -> DataS[Record]:
    Record.__signpost__ = sql.SQLSignpost(
        async_sessionmaker(sql_engine, expire_on_commit=False)
    )
    async with sql_engine.begin() as connection:
        await connection.run_sync(Record.__table__.create)
    return DataS(Record)


@pytest.fixture
async def team_records(sql_engine: AsyncEngine) -> DataS[TeamRecord]:
    backend = sql.SQLSignpost(
        async_sessionmaker(sql_engine, expire_on_commit=False)
    )
    async with sql_engine.begin() as connection:
        for entity in (League, Team, TeamRecord):
            entity.__signpost__ = backend
            await connection.run_sync(entity.__table__.create)
    return DataS(TeamRecord)
