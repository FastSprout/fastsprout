from contextlib import AbstractAsyncContextManager

import pytest
from docker.errors import NotFound
from sqlalchemy import text
from testcontainers.community.mysql import MySqlContainer

from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestMariaDB, TestMySQL, TestSQLDatabase

from .base_test_database import BaseTestSQLDatabase
from .conftest import ContextRecord


@pytest.mark.integration
class TestMySQLContext(BaseTestSQLDatabase):
    image = "mysql:8.4"

    def make_database(
        self,
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestMySQL(ContextRecord)

    @given("a database container with custom credentials")
    def server(self) -> MySqlContainer:
        return MySqlContainer(
            self.image,
            username="tester",
            password="test:password",
            dbname="heroes",
        )

    @when("a configured MySQL-compatible context fails inside its body")
    async def failed_context(
        self, server: MySqlContainer
    ) -> tuple[str, str, ValueError | None]:
        database_name, user, failure = "", "", None
        try:
            async with TestMySQL(ContextRecord, container=server) as database:
                async with database.session() as session:
                    database_name = str(
                        await session.scalar(text("SELECT DATABASE()"))
                    )
                    user = str(
                        await session.scalar(text("SELECT CURRENT_USER()"))
                    )
                raise ValueError("body failed")
        except ValueError as error:
            failure = error
        return database_name, user, failure

    @then("custom credentials work and a failed body releases resources")
    def test_configuration(
        self,
        server: MySqlContainer,
        failed_context: tuple[str, str, ValueError | None],
    ) -> None:
        database_name, user, failure = failed_context
        assert database_name == "heroes"
        assert user.startswith("tester@")
        assert isinstance(failure, ValueError)
        assert str(failure) == "body failed"
        with pytest.raises(NotFound):
            server.get_wrapped_container().reload()
        assert "__signpost__" not in vars(ContextRecord)


class TestMariaDBContext(TestMySQLContext):
    image = "mariadb:11.4"

    def make_database(
        self,
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestMariaDB(ContextRecord)
