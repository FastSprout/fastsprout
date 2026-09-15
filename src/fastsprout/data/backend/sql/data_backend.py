from abc import ABC
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, ClassVar, cast

from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.implementation.data_backend import BaseDataBackend
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.exceptions import NoSessionError

from .query import SQLQuery
from .session import SessionFactory as SessionFactory

__all__ = ["SQLDataBackend", "SessionFactory"]


class SQLDataBackend(BaseDataBackend, ABC):
    session_factory: ClassVar[
        Callable[[], AbstractAsyncContextManager[AsyncSession]] | None
    ] = None

    def __init__(
        self,
        *,
        session: AsyncSession | None = None,
    ) -> None:
        super().__init__()
        self._async_session: AsyncSession | None = session

    @asynccontextmanager
    async def bind(self) -> AsyncIterator["SQLDataBackend"]:
        """Signpost side of the backend: open a session for the context
        and yield a clone bound to it."""
        async with self._get_session_factory() as session:
            yield type(self)(session=session)

    def query_for[E: Entitieable[Any]](self, entity: type[E]) -> BaseQuery:
        return SQLQuery(entity=entity)  # pyright: ignore[reportArgumentType]

    def _get_session_factory(self) -> AbstractAsyncContextManager[AsyncSession]:
        """
        Returns an async session factory for the repository.
        If an async session is provided, it uses that;
        otherwise, it uses the factory.
        """
        return self.__make_session_factory()

    @asynccontextmanager
    async def _session_transaction(
        self,
        session: AsyncSession,
    ) -> AsyncIterator[AsyncSession]:
        if session.in_transaction():
            async with session.begin_nested():
                yield session
        else:
            async with session.begin():
                yield session

    @asynccontextmanager
    async def __make_session_factory(
        self,
    ) -> AsyncIterator[AsyncSession]:
        if self._async_session is not None:
            yield self._async_session
            return
        # getattr: pyright binds class-level callables as methods
        session_factory = cast(
            SessionFactory | None,
            getattr(type(self), "session_factory", None),
        )
        if session_factory is not None:
            async with session_factory() as session:
                yield session
            return
        raise NoSessionError(
            "No async session or factory provided for the sql a."
        )
