from typing import Any, Protocol, runtime_checkable

from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable

from .creatable import Creatable
from .deletable import Deletable
from .findable import Findable
from .iterable import Iterable
from .soft_deletable import SoftDeletable
from .streamable import Streamable
from .updatable import Updatable, UpdatableByQuery
from .upsertable import Upsertable

__all__ = ["Abilitable"]


@runtime_checkable
class Abilitable[E: Entitieable[Any], Q: BaseQuery](
    Creatable[E],
    Deletable[E, Q],
    Findable[E, Q],
    Iterable[E, Q],
    SoftDeletable[E, Q],
    Streamable[E, Q],
    Updatable[E],
    Upsertable[E],
    UpdatableByQuery[E, Q],
    Protocol,
): ...
