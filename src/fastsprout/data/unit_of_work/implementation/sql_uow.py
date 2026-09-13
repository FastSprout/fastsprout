from types import TracebackType
from typing import NotRequired, Self, TypedDict, Unpack

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastsprout.data.backend.sql.base import SQLBackend

from .simple_uow import SimpleUnitOfWork

__all__ = ["SQLUnitOfWork"]


class SQLUnitOfWorkParams(TypedDict):
    is_transaction: NotRequired[bool]
    session_factory: NotRequired[async_sessionmaker[AsyncSession] | None]


class SQLUnitOfWork(SimpleUnitOfWork[SQLBackend, *Unpack[SQLUnitOfWorkParams]]):
    """SQLAlchemy-backed unit of work.

    Equivalent of CobraPack's ``unit_of_work.BaseSQLUnitOfWork``.
    Repository attributes declared via ``Depends()`` are instantiated
    with the shared ``AsyncSession`` on ``begin``.
    """

    session_factory: async_sessionmaker[AsyncSession]

    def __init__(self, **kwargs: Unpack[SQLUnitOfWorkParams]):
        super().__init__(**kwargs)
        session_factory = kwargs.get("session_factory", None)
        if session_factory is not None:
            self.session_factory = session_factory
        self._is_transaction = kwargs.get("is_transaction", False)
        self._session: AsyncSession | None = None

    @property
    def is_transaction(self) -> bool:
        return self._is_transaction

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("Async session is not initialized")
        return self._session

    def _init_attr(self, class_: type[SQLBackend]) -> SQLBackend:
        return class_(async_session=self.session)

    def begin(
        self, is_transaction: bool | None = None, *args, **kwargs
    ) -> None:
        if self._session is not None:
            raise RuntimeError("Session is already initialized")
        if is_transaction is not None:
            self._is_transaction = is_transaction
        self._session = self.session_factory()
        super().begin()

    def close(self) -> None:
        if self.attrs_are_init and self.is_transaction:
            self.commit()
        if self._session is not None:
            self._session.sync_session.close()
            self._session = None
        super().close()

    async def acommit(self) -> None:
        try:
            await self.session.flush()
            await self.session.commit()
        except Exception:
            await self.arollback()
            raise

    async def arollback(self) -> None:
        await self.session.rollback()

    def commit(self) -> None:
        sync_session = self.session.sync_session
        try:
            sync_session.flush()
            sync_session.commit()
        except Exception:
            self.rollback()
            raise

    def rollback(self) -> None:
        self.session.sync_session.rollback()

    async def __aenter__(self) -> Self:
        self.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
