from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager

from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestSQLDatabase, TestSQLite

from .conftest import ContextRecord


class BaseTestSQLDatabase:
    def make_database(
        self,
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestSQLite(ContextRecord)

    @given("an isolated database for records")
    async def database(self) -> AsyncIterator[TestSQLDatabase[SQLSignpost]]:
        async with self.make_database() as database:
            yield database

    @when("a record is committed through DataR")
    async def committed_record(
        self, database: TestSQLDatabase[SQLSignpost]
    ) -> ContextRecord:
        async with DataR() as datar:
            record = await datar.ability(ContextRecord).create(
                ContextRecord(id=1, name="Ada")
            )
        return record

    @then("committed data remains visible in the same database context")
    async def test_commits(
        self,
        committed_record: ContextRecord,
        database: TestSQLDatabase[SQLSignpost],
    ) -> None:
        async with DataR() as datar:
            found = await datar.ability(ContextRecord).find_exactly_one(
                datar.ability(ContextRecord)
                .query_for()
                .where(ContextRecord.id.eq(committed_record.id))
            )
            assert found.name == "Ada"
        async with database.session() as session:
            assert session.sync_session.expire_on_commit is False

    @when("a committed database is closed and a fresh context is opened")
    async def reopened_database(
        self,
    ) -> AsyncIterator[TestSQLDatabase[SQLSignpost]]:
        async with self.make_database():
            async with DataR() as datar:
                await datar.ability(ContextRecord).create(
                    ContextRecord(id=1, name="Ada")
                )
        async with self.make_database() as database:
            yield database

    @then("a new database context does not retain a previous commit")
    async def test_isolation(
        self, reopened_database: TestSQLDatabase[SQLSignpost]
    ) -> None:
        async with DataR() as datar:
            assert (
                await datar.ability(ContextRecord).find_first(
                    datar.ability(ContextRecord).query_for()
                )
                is None
            )
