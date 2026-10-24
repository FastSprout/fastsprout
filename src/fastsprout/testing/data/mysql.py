from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import overload

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.mysql import MySqlContainer

from fastsprout.data.backend.sql import SQLSignpost

from .sql import SQLTestEntityable, TestSQLDatabase, connect, container_database

__all__ = ["TestMySQL"]


@overload
def mysql(
    *entities: SQLTestEntityable,
    signpost: None = None,
    container: MySqlContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "mysql:8.4",
) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]: ...


@overload
def mysql[S: SQLSignpost](
    *entities: SQLTestEntityable,
    signpost: type[S],
    container: MySqlContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "mysql:8.4",
) -> AbstractAsyncContextManager[TestSQLDatabase[S]]: ...


def mysql[S: SQLSignpost](
    *entities: SQLTestEntityable,
    signpost: type[S] | None = None,
    container: MySqlContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "mysql:8.4",
) -> (
    AbstractAsyncContextManager[TestSQLDatabase[S]]
    | AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]
):
    """Own a MySQL container with async sessions and selected entity tables."""
    server = container if container is not None else MySqlContainer(image)

    def url() -> str:
        return (
            make_url(server.get_connection_url())
            .set(drivername="mysql+asyncmy")
            .render_as_string(hide_password=False)
        )

    if signpost is None:
        return container_database(
            server,
            url,
            lambda url: connect(
                engine(url), entities, SQLSignpost, sessions=sessions
            ),
        )
    return container_database(
        server,
        url,
        lambda url: connect(engine(url), entities, signpost, sessions=sessions),
    )


TestMySQL = mysql
