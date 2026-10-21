from typing import Any, Protocol, runtime_checkable

from typing_extensions import TypeVar

from fastsprout.core import Undefined, UndefinedType
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable

from .creatable import Creatable
from .deletable import Deletable
from .findable import Findable
from .iterable import Iterable
from .streamable import Streamable
from .updatable import Updatable, UpdatableByQueryable
from .upsertable import Upsertable

__all__ = ["Abilitable"]

E = TypeVar("E", bound=Entitieable[Any])
Q = TypeVar("Q", bound=BaseQuery, contravariant=True)
QueryOut = TypeVar("QueryOut", bound=BaseQuery, default=Q, covariant=True)


@runtime_checkable
class Abilitable(
    Creatable[E],
    Deletable[E, Q],
    Findable[E, Q],
    Iterable[E, Q],
    Streamable[E, Q],
    Updatable[E],
    Upsertable[E],
    UpdatableByQueryable[E, Q],
    Protocol[E, Q, QueryOut],
):
    def query_for(
        self, entity: type[E] | UndefinedType = Undefined
    ) -> QueryOut:
        """Create a query for the explicit entity or this ability's owner."""
        ...
