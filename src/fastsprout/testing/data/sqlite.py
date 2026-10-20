from collections.abc import Callable
from typing import overload

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastsprout.data.backend.sql import SQLEntity, SQLSignpost

from .sql import TestSQLDatabase, connect

__all__ = ["TestSQLite"]


@overload
def sqlite(
    *entities: type[SQLEntity],
    signpost: None = None,
    engine: AsyncEngine | None = None,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    echo: bool = False,
    expire_on_commit: bool = False,
) -> TestSQLDatabase[SQLSignpost]: ...


@overload
def sqlite[S: SQLSignpost](
    *entities: type[SQLEntity],
    signpost: type[S],
    engine: AsyncEngine | None = None,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    echo: bool = False,
    expire_on_commit: bool = False,
) -> TestSQLDatabase[S]: ...


def sqlite[S: SQLSignpost](
    *entities: type[SQLEntity],
    signpost: type[S] | None = None,
    engine: AsyncEngine | None = None,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    echo: bool = False,
    expire_on_commit: bool = False,
) -> TestSQLDatabase[S] | TestSQLDatabase[SQLSignpost]:
    """Create an isolated SQLite context; supplied engines stay caller-owned."""
    connection = (
        engine
        if engine is not None
        else create_async_engine("sqlite+aiosqlite:///:memory:", echo=echo)
    )
    return connect(
        connection,
        entities,
        SQLSignpost if signpost is None else signpost,
        sessions=sessions,
        expire_on_commit=expire_on_commit,
        dispose=engine is None,
    )


TestSQLite = sqlite
