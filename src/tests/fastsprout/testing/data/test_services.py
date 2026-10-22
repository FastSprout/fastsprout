import os
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.testing.core import then, when
from fastsprout.testing.data import TestSQLDatabase
from fastsprout.testing.data.sql import connect
from tests.services import wait_for_service

from .base_test_database import BaseTestSQLDatabase
from .conftest import ContextRecord


@asynccontextmanager
async def database_service() -> AsyncIterator[TestSQLDatabase[SQLSignpost]]:
    engine = create_async_engine(os.environ["TEST_SERVICE_URL"])

    async def connected() -> None:
        async with engine.connect():
            pass

    try:
        await wait_for_service(connected)
        async with connect(
            engine, (ContextRecord,), SQLSignpost, dispose=False
        ) as database:
            yield database
    finally:
        await engine.dispose()


@pytest.mark.integration
class TestSQLService(BaseTestSQLDatabase):
    def make_database(
        self,
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return database_service()

    @when("a failed database context is followed by a new context")
    async def after_failure(
        self,
    ) -> AsyncIterator[TestSQLDatabase[SQLSignpost]]:
        with pytest.raises(ValueError, match="body failed"):
            async with self.make_database():
                async with DataR() as datar:
                    await datar.ability(ContextRecord).create(
                        ContextRecord(id=1, name="committed before failure")
                    )
                raise ValueError("body failed")
        assert "__signpost__" not in vars(ContextRecord)
        async with self.make_database() as database:
            yield database

    @then("failure removes committed rows and restores the entity binding")
    async def test_failure_isolation(
        self, after_failure: TestSQLDatabase[SQLSignpost]
    ) -> None:
        async with DataR() as datar:
            assert (
                await datar.ability(ContextRecord).find_first(
                    datar.ability(ContextRecord).query_for()
                )
                is None
            )
