from typing import Any, Protocol, runtime_checkable

from fastsprout.core.types import IdentificatorType
from fastsprout.data.entity import Entitieable

__all__ = ["Gettable"]


@runtime_checkable
class Gettable[
    E: Entitieable,
    ID: IdentificatorType | Any,
](Protocol):
    async def get_by_id(self, id: ID, /) -> E | None: ...
    async def get_by_id_or_raise(self, id: ID, /) -> E: ...
