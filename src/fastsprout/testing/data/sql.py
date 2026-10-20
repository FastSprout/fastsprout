from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import AsyncExitStack, asynccontextmanager
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from testcontainers.core.container import DockerContainer

from fastsprout.data.backend.sql import SQLEntity, SQLSignpost
from fastsprout.data.backend.sql.entity import (
    SQL_ENTITY_REGISTRY,
    validate_source_type,
)
from fastsprout.testing.container import container_context

__all__ = ["TestSQLDatabase", "connect", "container_database"]


@asynccontextmanager
async def container_database[S: SQLSignpost](
    container: DockerContainer,
    url: Callable[[], str],
    database: Callable[[str], "TestSQLDatabase[S]"],
) -> AsyncIterator["TestSQLDatabase[S]"]:
    async with container_context(container):
        async with database(url()) as context:
            yield context


def connect[S: SQLSignpost](
    engine: AsyncEngine,
    entities: Sequence[type[SQLEntity]],
    signpost: type[S],
    *,
    sessions: Callable[[AsyncEngine], async_sessionmaker[AsyncSession]]
    | None = None,
    expire_on_commit: bool = False,
    dispose: bool = True,
) -> "TestSQLDatabase[S]":
    factory = (
        sessions(engine)
        if sessions is not None
        else async_sessionmaker(engine, expire_on_commit=expire_on_commit)
    )
    return TestSQLDatabase(
        engine, factory, signpost(factory), entities, dispose=dispose
    )


class TestSQLDatabase[S: SQLSignpost]:
    """Own a test database and temporarily bind its selected entities."""

    __test__ = False

    def __init__(
        self,
        engine: AsyncEngine,
        session: async_sessionmaker[AsyncSession],
        signpost: S,
        entities: Sequence[type[SQLEntity]],
        *,
        dispose: bool = True,
    ) -> None:
        self.engine = engine
        self.session = session
        self.signpost = signpost
        self.entities = tuple(entities)
        self.dispose = dispose
        self.resources = AsyncExitStack()
        self.active = False

    async def __aenter__(self) -> Self:
        if self.active:
            raise RuntimeError("Database context is already entered")
        self.active = True
        try:
            if self.dispose:
                self.resources.push_async_callback(self.engine.dispose)
            for entity in self.entities:
                validate_source_type(entity, self.signpost)
            async with self.engine.begin() as connection:
                await connection.run_sync(
                    lambda connection: SQL_ENTITY_REGISTRY.metadata.create_all(
                        connection,
                        tables=[entity.__table__ for entity in self.entities],
                        checkfirst=False,
                    )
                )
            self.resources.push_async_callback(self.drop_tables)
            self.bind()
            return self
        except BaseException:
            await self.resources.aclose()
            self.active = False
            raise

    def bind(self) -> None:
        for entity in self.entities:
            previous = vars(entity).get("__signpost__")
            if previous is None:
                self.resources.callback(delattr, entity, "__signpost__")
            else:
                self.resources.callback(
                    setattr, entity, "__signpost__", previous
                )
            entity.__signpost__ = self.signpost

    async def drop_tables(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(
                lambda connection: SQL_ENTITY_REGISTRY.metadata.drop_all(
                    connection,
                    tables=[entity.__table__ for entity in self.entities],
                )
            )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            await self.resources.__aexit__(exc_type, exc, traceback)
        finally:
            self.active = False
