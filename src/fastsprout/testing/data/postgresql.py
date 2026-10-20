from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from functools import partial
from typing import overload

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.postgres import PostgresContainer

from fastsprout.data.backend.sql import SQLEntity, SQLSignpost

from .sql import TestSQLDatabase, connect, container_database

__all__ = ["TestPostgreSQL", "postgres_context"]


@overload
def postgresql(
    *entities: type[SQLEntity],
    signpost: None = None,
    container: PostgresContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "postgres:18-alpine",
) -> AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]: ...


@overload
def postgresql[S: SQLSignpost](
    *entities: type[SQLEntity],
    signpost: type[S],
    container: PostgresContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "postgres:18-alpine",
) -> AbstractAsyncContextManager[TestSQLDatabase[S]]: ...


def postgresql[S: SQLSignpost](
    *entities: type[SQLEntity],
    signpost: type[S] | None = None,
    container: PostgresContainer | None = None,
    engine: Callable[[str], AsyncEngine] = create_async_engine,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    image: str = "postgres:18-alpine",
) -> (
    AbstractAsyncContextManager[TestSQLDatabase[S]]
    | AbstractAsyncContextManager[TestSQLDatabase[SQLSignpost]]
):
    """Own a PostgreSQL container; pass configured factories for native options."""
    postgres = (
        container
        if container is not None
        else PostgresContainer(image, driver=None)
    )
    if signpost is None:
        return postgres_context(
            postgres,
            lambda url: connect(
                engine(url),
                entities,
                SQLSignpost,
                sessions=sessions,
            ),
        )
    return postgres_context(
        postgres,
        lambda url: connect(
            engine(url),
            entities,
            signpost,
            sessions=sessions,
        ),
    )


def postgres_context[S: SQLSignpost](
    container: PostgresContainer,
    database: Callable[[str], TestSQLDatabase[S]],
) -> AbstractAsyncContextManager[TestSQLDatabase[S]]:
    return container_database(
        container,
        partial(container.get_connection_url, driver="asyncpg"),
        database,
    )


TestPostgreSQL = postgresql
