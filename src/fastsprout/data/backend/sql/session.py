from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["SessionFactory"]

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]
