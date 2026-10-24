from contextlib import AbstractAsyncContextManager

import pytest
from docker.errors import NotFound
from sqlalchemy import text
from testcontainers.community.oracle import OracleDbContainer

from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import TestOracle, TestSQLDatabase

from .base_test_database import BaseTestSQLDatabase
from .conftest import ContextRecord


@pytest.mark.integration
@pytest.mark.docker
class TestOracleContext(BaseTestSQLDatabase):
    def make_database(
        self,
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestOracle(ContextRecord)

    @given("an Oracle Free container with a dedicated application user")
    def server(self) -> OracleDbContainer:
        return OracleDbContainer(
            "gvenzl/oracle-free:23-slim-faststart",
            username="tester",
            password="testing_password",
        )

    @when("a configured Oracle context fails inside its body")
    async def failed_context(
        self, server: OracleDbContainer
    ) -> tuple[str, bool, ValueError | None]:
        user, asynchronous, failure = "", False, None
        try:
            async with TestOracle(ContextRecord, container=server) as database:
                async with database.session() as session:
                    user = str(
                        await session.scalar(text("SELECT USER FROM dual"))
                    )
                    asynchronous = database.engine.dialect.is_async
                raise ValueError("body failed")
        except ValueError as error:
            failure = error
        return user, asynchronous, failure

    @then("custom credentials work and a failed body releases resources")
    def test_configuration(
        self,
        server: OracleDbContainer,
        failed_context: tuple[str, bool, ValueError | None],
    ) -> None:
        user, asynchronous, failure = failed_context
        assert user == "TESTER"
        assert asynchronous
        assert isinstance(failure, ValueError)
        assert str(failure) == "body failed"
        with pytest.raises(NotFound):
            server.get_wrapped_container().reload()
        assert "__signpost__" not in vars(ContextRecord)
