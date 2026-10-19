from contextlib import AbstractAsyncContextManager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.core import Undefined, UndefinedType
from fastsprout.data.backend.protocols import DataAbilitable
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.finalizer import SQLFinalizable
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.entity import Signpostable
from fastsprout.events import EventBus

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
):
    def __init__(
        self,
        signpost: Signpostable[AbstractAsyncContextManager[AsyncSession]],
        *,
        entity: type[E] | UndefinedType = Undefined,
        bus: EventBus | UndefinedType | None = Undefined,
    ) -> None:
        # Protocol initializers interrupt the cooperative constructor chain.
        SQLDataBackend.__init__(self, signpost, bus=bus)
        self.entity = entity

    def query_for(
        self, entity: type[E] | UndefinedType = Undefined
    ) -> SQLQuery[E]:
        source = self.entity if isinstance(entity, UndefinedType) else entity
        if isinstance(source, UndefinedType):
            raise TypeError(
                "query_for() requires an entity on an unbound ability"
            )
        return SQLQuery(source)
