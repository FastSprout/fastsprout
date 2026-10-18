from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.protocols import Finalizable

__all__ = ["SQLFinalizable", "TransactionState"]


@runtime_checkable
class TransactionState(Protocol):
    @property
    def in_transaction(self) -> bool: ...


class SQLFinalizable(Finalizable):
    def __init__(self, session: AsyncSession, /) -> None:
        self.db_session = session
        self.after_commit: list[Callable[[], Awaitable[None]]] = []

    async def finalize(self) -> None:
        callbacks, self.after_commit = self.after_commit, []
        await self.db_session.commit()
        for callback in callbacks:
            await callback()

    async def abort(self) -> None:
        self.after_commit.clear()
        await self.db_session.rollback()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        yield self.db_session

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        if not self.db_session.in_transaction():
            await self.db_session.begin()
        connection = await self.db_session.connection()
        if connection.dialect.name == "sqlite":
            raw = await connection.get_raw_connection()
            driver = raw.driver_connection
            # SQLite legacy mode does not start a transaction for SELECT or SAVEPOINT.
            if (
                isinstance(driver, TransactionState)
                and not driver.in_transaction
            ):
                await connection.exec_driver_sql("BEGIN")
        async with self.db_session.begin_nested():
            yield self.db_session
