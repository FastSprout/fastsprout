from typing import Generic, Protocol, runtime_checkable

from typing_extensions import TypeVar

from fastsprout.core import UndefinedType
from fastsprout.data.backend.protocols.backendable import Backendable
from fastsprout.data.backend.protocols.finalizable import Finalizable
from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.capabilities.protocols import Abilitable
from fastsprout.data.entity import Entitieable

__all__ = ["DataAbilitable"]

E = TypeVar("E", bound=Entitieable)
T = TypeVar("T", covariant=True)
Q = TypeVar("Q", bound=BaseQuery, contravariant=True)
F = TypeVar("F", bound=Finalizable, covariant=True)
QueryOut = TypeVar("QueryOut", bound=BaseQuery, default=Q, covariant=True)


@runtime_checkable
class DataAbilitable(
    Abilitable[E, Q, QueryOut],
    Backendable[T, F],
    Protocol,
    # Generic fixes parameter order when inheriting protocols on Python 3.12.
    Generic[E, T, Q, F, QueryOut],
):
    entity: type[E] | UndefinedType
