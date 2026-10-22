from asyncio import CancelledError, Event, create_task, to_thread
from contextlib import AbstractAsyncContextManager
from threading import Event as ThreadEvent

import pytest
from docker.errors import NotFound
from sqlalchemy import text
from testcontainers.community.postgres import PostgresContainer

from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestPostgreSQL, TestSQLDatabase

from .base_test_database import BaseTestSQLDatabase
from .conftest import ContextRecord


@pytest.mark.integration
@pytest.mark.docker
class TestPostgreSQLContext(BaseTestSQLDatabase):
    def make_database(
        self,
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestPostgreSQL(ContextRecord)

    @given("a PostgreSQL container with custom credentials")
    def postgres(self) -> PostgresContainer:
        return PostgresContainer(
            "postgres:18-alpine",
            username="tester",
            password="testing",
            dbname="heroes",
            driver=None,
        )

    @when("a configured PostgreSQL context fails inside its body")
    async def failed_context(
        self, postgres: PostgresContainer
    ) -> tuple[str, str, ValueError | None]:
        user, database_name, failure = "", "", None
        try:
            async with TestPostgreSQL(
                ContextRecord, container=postgres
            ) as database:
                async with database.session() as session:
                    user = str(
                        await session.scalar(text("SELECT current_user"))
                    )
                    database_name = str(
                        await session.scalar(text("SELECT current_database()"))
                    )
                raise ValueError("body failed")
        except ValueError as error:
            failure = error
        return user, database_name, failure

    @then("a configured container is stopped after a body failure")
    def test_configuration(
        self,
        postgres: PostgresContainer,
        failed_context: tuple[str, str, ValueError | None],
    ) -> None:
        user, database_name, failure = failed_context
        assert user == "tester"
        assert database_name == "heroes"
        assert isinstance(failure, ValueError)
        assert str(failure) == "body failed"
        with pytest.raises(NotFound):
            postgres.get_wrapped_container().reload()
        assert "__signpost__" not in vars(ContextRecord)

    @when("container startup is cancelled")
    async def cancelled_startup(
        self, postgres: PostgresContainer, monkeypatch: pytest.MonkeyPatch
    ) -> CancelledError | None:
        started = ThreadEvent()
        original = postgres.start

        def start() -> PostgresContainer:
            started.set()
            return original()

        async def use_database() -> None:
            async with TestPostgreSQL(ContextRecord, container=postgres):
                await Event().wait()

        monkeypatch.setattr(postgres, "start", start)
        task = create_task(use_database())
        await to_thread(started.wait)
        task.cancel()
        try:
            await task
        except CancelledError as error:
            return error
        return None

    @then("cancellation during startup still removes the container")
    def test_cancel_startup(
        self,
        postgres: PostgresContainer,
        cancelled_startup: CancelledError | None,
    ) -> None:
        assert isinstance(cancelled_startup, CancelledError)
        with pytest.raises(NotFound):
            postgres.get_wrapped_container().reload()
        assert "__signpost__" not in vars(ContextRecord)
