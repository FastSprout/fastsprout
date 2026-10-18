from contextlib import AbstractAsyncContextManager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.protocols import DataAbilitable
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.finalizer import SQLFinalizable
from fastsprout.data.backend.sql.query import SQLQuery

from .creatable import SQLCreatable
from .deletable import SQLDeletable
from .findable import SQLFindable
from .iterable import SQLIterable
from .streamable import SQLStreamable
from .updatable import SQLUpdatable, SQLUpdatableByQuery
from .upsertable import SQLUpsertable

__all__ = ["SQLAbilitable"]


class SQLAbilitable[E: SQLEntity[Any]](
    DataAbilitable[
        E,
        AbstractAsyncContextManager[AsyncSession],
        SQLQuery[E],
        SQLFinalizable,
    ],
    SQLCreatable[E],
    SQLDeletable[E],
    SQLFindable[E],
    SQLIterable[E],
    SQLStreamable[E],
    SQLUpdatable[E],
    SQLUpsertable[E],
    SQLUpdatableByQuery[E],
): ...
