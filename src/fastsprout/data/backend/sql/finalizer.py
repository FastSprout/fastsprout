from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.protocols import Finalizable

__all__ = ["SQLFinalizable"]


class SQLFinalizable(Finalizable):
    def __init__(self, session: AsyncSession, /) -> None:
        self.__session = session

    async def finalize(self) -> None:
        await self.__session.commit()

    async def abort(self) -> None:
        await self.__session.rollback()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        yield self.__session

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        if self.__session.in_transaction():
            # one savepoint per operation — a state you can roll back to,
            # like a commit in a git branch
            async with self.__session.begin_nested():
                yield self.__session
        else:
            # open the outer transaction and KEEP it open — the
            # finalizer (finalize/abort) owns its end, not the operation
            await self.__session.begin()
            yield self.__session
