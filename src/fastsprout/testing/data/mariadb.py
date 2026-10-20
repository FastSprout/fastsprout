from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import overload

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.mysql import MySqlContainer

from fastsprout.data.backend.sql import SQLEntity, SQLSignpost

from .mysql import TestMySQL
from .sql import TestSQLDatabase

__all__ = ["TestMariaDB"]


@overload
def mariadb(
    *entities: type[SQLEntity],
    signpost: None = None,
    container: MySqlContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "mariadb:11.4",
) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]: ...


@overload
def mariadb[S: SQLSignpost](
    *entities: type[SQLEntity],
    signpost: type[S],
    container: MySqlContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "mariadb:11.4",
) -> AbstractAsyncContextManager[TestSQLDatabase[S]]: ...


def mariadb[S: SQLSignpost](
    *entities: type[SQLEntity],
    signpost: type[S] | None = None,
    container: MySqlContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "mariadb:11.4",
) -> (
    AbstractAsyncContextManager[TestSQLDatabase[S]]
    | AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]
):
    """Reuse the MySQL context lifecycle with a MariaDB server."""
    if signpost is None:
        return TestMySQL(
            *entities,
            container=container,
            engine=engine,
            sessions=sessions,
            image=image,
        )
    return TestMySQL(
        *entities,
        signpost=signpost,
        container=container,
        engine=engine,
        sessions=sessions,
        image=image,
    )


TestMariaDB = mariadb
