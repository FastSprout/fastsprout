from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import overload

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.oracle import OracleDbContainer

from fastsprout.data.backend.sql import SQLSignpost

from .sql import SQLTestEntityable, TestSQLDatabase, connect, container_database

__all__ = ["TestOracle"]


@overload
def oracle(
    *entities: SQLTestEntityable,
    signpost: None = None,
    container: OracleDbContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "gvenzl/oracle-free:23-slim-faststart",
) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]: ...


@overload
def oracle[S: SQLSignpost](
    *entities: SQLTestEntityable,
    signpost: type[S],
    container: OracleDbContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "gvenzl/oracle-free:23-slim-faststart",
) -> AbstractAsyncContextManager[TestSQLDatabase[S]]: ...


def oracle[S: SQLSignpost](
    *entities: SQLTestEntityable,
    signpost: type[S] | None = None,
    container: OracleDbContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "gvenzl/oracle-free:23-slim-faststart",
) -> (
    AbstractAsyncContextManager[TestSQLDatabase[S]]
    | AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]
):
    """Own an Oracle Free container with async sessions and selected tables."""
    server = (
        container
        if container is not None
        else OracleDbContainer(
            image, username="test", password="testing_password"
        )
    )
    if signpost is None:
        return container_database(
            server,
            server.get_connection_url,
            lambda url: connect(
                engine(url), entities, SQLSignpost, sessions=sessions
            ),
        )
    return container_database(
        server,
        server.get_connection_url,
        lambda url: connect(engine(url), entities, signpost, sessions=sessions),
    )


TestOracle = oracle
