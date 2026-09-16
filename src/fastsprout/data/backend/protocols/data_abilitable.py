from typing import Protocol, runtime_checkable

from fastsprout.data.backend.protocols import Backendable, Finalizable
from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.capabilities.protocols import Abilitable
from fastsprout.data.entity import Entitieable

__all__ = ["DataAbilitable"]


@runtime_checkable
class DataAbilitable[E: Entitieable, T, Q: BaseQuery, F: Finalizable](
    Abilitable[E, Q], Backendable[T, F], Protocol
):
    pass
