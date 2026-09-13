from typing import Any

from fastsprout.core.types import IdentificatorType
from fastsprout.data.backend.sql.base import SQLBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.capabilities.protocols import Gettable

__all__ = ["SQLGettable"]


class SQLGettable[
    E: SQLEntity[Any],
    ID: IdentificatorType | Any,
](Gettable[E, ID], SQLBackend[E]):
    async def get_by_id(self, id: ID, /) -> E | None: ...
    async def get_by_id_or_raise(self, id: ID, /) -> E: ...
