from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from copy import copy
from typing import Annotated, Generic, Protocol, Self, runtime_checkable

from annotated_types import Ge
from typing_extensions import TypeVar

from fastsprout.core import Undefined, UndefinedType, dataclass
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types import OrderedValue
from fastsprout.data.entity import Entitieable, Signpostable
from fastsprout.data.streams.protocols import AsyncJoinedStreamable

from .operators import And, Eq, Gt, Lt, Nand, Or, Xor
from .predicate import Expression, FieldPredicate

__all__ = ["BaseQuery", "JoinedQueryable"]

E = TypeVar("E", bound=Entitieable)
StatementT = TypeVar("StatementT")
# TypeVar defaults preserve two-parameter queries on Python 3.12.
RowT = TypeVar("RowT", default=None)


@dataclass
class BaseQuery(ABC, Generic[E, StatementT, RowT]):
    """Shared query builder; RowT distinguishes tuple rows from entity reads."""

    And = And
    Or = Or
    Xor = Xor
    Nand = Nand

    entity: type[E]
    statement: StatementT | None = None
    limit_value: int | UndefinedType | None = Undefined
    offset_value: Annotated[int, Ge(0)] = 0
    conditions: tuple[Expression[E], ...] = ()
    orderings: tuple[tuple[str, bool], ...] = ()

    def copy(self) -> Self:
        return copy(self)

    def unpaged(self) -> Self:
        return self.copy().offset(0).limit(None)

    def unfiltered(self) -> Self:
        query = self.copy()
        query.conditions = ()
        return query

    def where(self, *conditions: Expression[E]) -> Self:
        self.conditions += conditions
        return self

    def order_by[T: OrderedValue, Orm](
        self, field: FieldRef[E, T, Orm], *, reverse: bool = False
    ) -> Self:
        if field.entity_cls is not self.entity:
            raise TypeError("Sort field must belong to the query entity")
        self.orderings += ((field.name, reverse),)
        return self

    def after(self, cursor: E) -> Self:
        if not isinstance(cursor, self.entity):
            raise TypeError("Cursor must belong to the query entity")
        self.orderings = self.effective_orderings or (("id", False),)
        prefix: list[Expression[E]] = []
        alternatives: list[Expression[E]] = []
        for name, reverse in self.orderings:
            value = getattr(cursor, name)
            comparison = Lt(value) if reverse else Gt(value)
            alternatives.append(
                And(*prefix, FieldPredicate(self.entity, name, comparison))
            )
            prefix.append(FieldPredicate(self.entity, name, Eq(value)))
        return self.where(Or(*alternatives))

    @property
    def effective_orderings(self) -> tuple[tuple[str, bool], ...]:
        if self.orderings and not any(
            name == "id" for name, _ in self.orderings
        ):
            return (*self.orderings, ("id", False))
        return self.orderings

    def limit(self, max_n: Annotated[int, Ge(0)] | None = 1) -> Self:
        if max_n is not None and max_n < 0:
            raise ValueError("limit must be non-negative")
        self.limit_value = max_n
        return self

    def offset(self, to: Annotated[int, Ge(0)] = 0) -> Self:
        if to < 0:
            raise ValueError("offset must be non-negative")
        self.offset_value = to
        return self

    @abstractmethod
    def build(self) -> StatementT: ...


@runtime_checkable
class JoinedQueryable[E: Entitieable, ProductT, *Ts](Protocol):
    """Bind a multi-entity query to a routed backend context."""

    @property
    def entity(self) -> type[E]: ...

    def stream(
        self, signpost: Signpostable[AbstractAsyncContextManager[ProductT]]
    ) -> AsyncJoinedStreamable[*Ts]: ...
