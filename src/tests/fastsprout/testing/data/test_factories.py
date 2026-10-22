from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.community.mysql import MySqlContainer
from testcontainers.community.oracle import OracleDbContainer
from testcontainers.community.postgres import PostgresContainer

from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.testing.core import given, then, when
from fastsprout.testing.data import (
    TestMariaDB,
    TestMySQL,
    TestOracle,
    TestPostgreSQL,
    TestSQLDatabase,
)

from ..common import RecordedContainer
from .conftest import CRM, ContextRecord


class RecordedDatabase(RecordedContainer):
    url: str

    def get_connection_url(
        self, host: str | None = None, driver: str | None = None
    ) -> str:
        return self.url


class MySQLServer(RecordedDatabase, MySqlContainer):
    url = "mysql+pymysql://tester:secret@localhost/heroes"


class PostgreSQLServer(RecordedDatabase, PostgresContainer):
    url = "postgresql+asyncpg://tester:secret@localhost/heroes"


class OracleServer(RecordedDatabase, OracleDbContainer):
    url = "oracle+oracledb://tester:secret@localhost/heroes"


class BaseTestDatabaseFactory[C: RecordedDatabase]:
    server_type: type[C]
    expected_url: str

    def make_database(
        self,
        server: C,
        signpost: type[SQLSignpost] | None,
        engine: Callable[[str], AsyncEngine],
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        raise NotImplementedError

    @given("a container recording its lifecycle without starting Docker")
    def server(self) -> C:
        return self.server_type()

    @given("a recorder of URLs passed to the caller's engine factory")
    def urls(self) -> list[str]:
        return []

    @when("the database factory uses a default or custom signpost and engine")
    async def configured(
        self, server: C, custom: bool, urls: list[str]
    ) -> type[SQLSignpost]:
        def engine(url: str) -> AsyncEngine:
            urls.append(url)
            return create_async_engine("sqlite+aiosqlite:///:memory:")

        async with self.make_database(
            server, CRM if custom else None, engine
        ) as database:
            async with database.session() as session:
                session.add(ContextRecord(id=1, name="configured"))
                await session.commit()
            return type(database.signpost)

    @pytest.mark.parametrize("custom", [False, True])
    @then(
        "configuration is forwarded and database and container resources are released"
    )
    def test_configuration(
        self,
        server: C,
        custom: bool,
        configured: type[SQLSignpost],
        urls: list[str],
    ) -> None:
        assert configured is (CRM if custom else SQLSignpost)
        assert urls == [self.expected_url]
        assert server.calls == ["start", "stop"]
        assert "__signpost__" not in vars(ContextRecord)


class TestMySQLFactory(BaseTestDatabaseFactory[MySQLServer]):
    server_type = MySQLServer
    expected_url = "mysql+asyncmy://tester:secret@localhost/heroes"

    def make_database(
        self,
        server: MySQLServer,
        signpost: type[SQLSignpost] | None,
        engine: Callable[[str], AsyncEngine],
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestMySQL(
            ContextRecord, container=server, signpost=signpost, engine=engine
        )


class TestMariaDBFactory(TestMySQLFactory):
    def make_database(
        self,
        server: MySQLServer,
        signpost: type[SQLSignpost] | None,
        engine: Callable[[str], AsyncEngine],
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestMariaDB(
            ContextRecord, container=server, signpost=signpost, engine=engine
        )


class TestPostgreSQLFactory(BaseTestDatabaseFactory[PostgreSQLServer]):
    server_type = PostgreSQLServer
    expected_url = PostgreSQLServer.url

    def make_database(
        self,
        server: PostgreSQLServer,
        signpost: type[SQLSignpost] | None,
        engine: Callable[[str], AsyncEngine],
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestPostgreSQL(
            ContextRecord, container=server, signpost=signpost, engine=engine
        )


class TestOracleFactory(BaseTestDatabaseFactory[OracleServer]):
    server_type = OracleServer
    expected_url = OracleServer.url

    def make_database(
        self,
        server: OracleServer,
        signpost: type[SQLSignpost] | None,
        engine: Callable[[str], AsyncEngine],
    ) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]:
        return TestOracle(
            ContextRecord, container=server, signpost=signpost, engine=engine
        )
