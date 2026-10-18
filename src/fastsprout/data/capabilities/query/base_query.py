from abc import ABC, abstractmethod
from copy import copy
from typing import Annotated, Any, Self

from annotated_types import Ge

from fastsprout.core import Undefined, UndefinedType, dataclass
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types import OrderedValue
from fastsprout.data.entity import Entitieable

from .operators import And, Eq, Gt, Lt, Nand, Or, Xor
from .predicate import Expression, FieldPredicate

__all__ = ["BaseQuery"]


@dataclass
class BaseQuery[E: Entitieable[Any], StatementT](ABC):
    """Backend query with shared predicates and pagination."""

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
