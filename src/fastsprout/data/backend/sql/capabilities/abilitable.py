from typing import Any

from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery

from .creatable import SQLCreatable
from .deletable import SQLDeletable
from .findable import SQLFindable
from .iterable import SQLIterable
from .soft_deletable import SQLSoftDeletable
from .streamable import SQLStreamable
from .updatable import SQLUpdatable, SQLUpdatableByQuery
from .upsertable import SQLUpsertable

__all__ = ["SQLAbilitable"]


class SQLAbilitable[E: SQLEntity[Any], Q: SQLQuery[SQLEntity[Any]]](
    SQLCreatable[E],
    SQLDeletable[E, Q],
    SQLFindable[E, Q],
    SQLIterable[E, Q],
    SQLSoftDeletable[E, Q],  # pyright: ignore[reportInvalidTypeArguments]
    SQLStreamable[E, Q],
    SQLUpdatable[E],
    SQLUpsertable[E],
    SQLUpdatableByQuery[E, Q],
): ...
