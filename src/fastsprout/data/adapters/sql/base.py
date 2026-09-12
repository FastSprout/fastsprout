from abc import ABC
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.adapters.base import BaseAdapter
from fastsprout.data.adapters.sql.query import SQLQuery
from fastsprout.data.exceptions import NoSessionError

from .entity import SQLEntity

__all__ = ["SQLAdapter"]


class SQLAdapter[E: SQLEntity[Any]](BaseAdapter[E, SQLQuery[E]], ABC):
    session_factory: (
        Callable[[], AbstractAsyncContextManager[AsyncSession]] | None
    ) = None

    def __init__(
        self,
        *,
        async_session: AsyncSession | None = None,
    ) -> None:
        self._async_session: AsyncSession | None = async_session

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
        if self.session_factory is not None:
            async with self.session_factory() as session:
                yield session
            return
        raise NoSessionError(
            "No async session or factory provided for the sql adapter."
        )

    @property
    def default_query(self) -> SQLQuery[E]:
        return SQLQuery[E](entity=self.entity)
