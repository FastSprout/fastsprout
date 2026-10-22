from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from fastsprout.actions import DataS
from fastsprout.core import inject_depends
from fastsprout.data import DataR, provide_datar
from fastsprout.testing.core import given, when
from fastsprout.testing.data import TestSQLite

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


@given("an empty SQL-backed data service")
async def records(sql_engine: AsyncEngine) -> AsyncIterator[DataS[Record]]:
    async with TestSQLite(Record, engine=sql_engine):
        yield DataS(Record)


@given("a shared DataR transaction for the data service")
async def active_datar(records: DataS[Record]) -> AsyncIterator[DataR]:
    async with DataR() as datar:
        yield datar


@when("three records with distinct scores are persisted")
async def scored_records(
    records: DataS[Record],
    active_datar: DataR,
) -> DataS[Record]:
    for name, score in (("Batman", 20), ("Batgirl", 30), ("Robin", 40)):
        await records.create(Record(name=name, score=score), datar=active_datar)
    return records


@given("a SQL-backed data service with related entities")
async def team_records(
    sql_engine: AsyncEngine,
) -> AsyncIterator[DataS[TeamRecord]]:
    async with TestSQLite(League, Team, TeamRecord, engine=sql_engine):
        yield DataS(TeamRecord)
