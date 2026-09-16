from abc import ABC
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.implementation.data_backend import BaseDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.finalizer import SQLFinalizable

from .query import SQLQuery

__all__ = ["SQLDataBackend"]


class SQLDataBackend(
    BaseDataBackend[AbstractAsyncContextManager[AsyncSession], SQLFinalizable],
    ABC,
):
    @asynccontextmanager
    async def bind(self):
        """Signpost side of the backend: open a session for the context
        and yield a clone bound to it."""
        async with self._signpost.factory() as session:
            yield SQLFinalizable(session)

    @asynccontextmanager
    async def session(self):
        async with self.bind() as flow:
            async with flow.session() as session:
                yield session

    @asynccontextmanager
    async def transaction(self):
        async with self.bind() as flow:
            async with flow.transaction() as transaction:
                yield transaction

    def query_for[E: SQLEntity[Any]](self, entity: type[E]) -> SQLQuery[E]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return SQLQuery[E](entity=entity)
