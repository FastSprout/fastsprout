from collections.abc import Callable, Sequence
from enum import Enum
from typing import Any

from sqlalchemy import and_, false, func, not_, or_, select, true
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.selectable import Select

from fastsprout.core import UndefinedType, dataclass
from fastsprout.core.types import FilterValue
from fastsprout.data.capabilities.query import (
    And,
    BaseQuery,
    Expression,
    FieldPredicate,
    Filter,
    In,
    Not,
    Or,
    Xor,
)
from fastsprout.data.capabilities.query.operators import (
    Comparison,
    ComparisonKind,
)

from .entity import SQLEntity, validate_source

__all__ = ["SQLQuery", "compile_predicate"]


@dataclass
class SQLQuery[E: SQLEntity[Any]](BaseQuery[E, Select[tuple[E]]]):
    @property
    def native_conditions(self) -> bool:
        return (
            compile_predicate(
                And(*self.conditions),
                self.entity,
                lambda name: self.entity.__table__.c[name],
            )
            is not None
        )

    def build(self) -> Select[tuple[E]]:
        validate_source(self.entity)
        statement = (
            self.statement
            if self.statement is not None
            else select(self.entity)
        )
        predicate = compile_predicate(
            And(*self.conditions),
            self.entity,
            lambda name: statement.selected_columns[name],
        )
        if predicate is None:
            raise TypeError(
                "Python predicates require query execution through stream()"
            )
        statement = statement.where(predicate)
        if self.orderings:
            statement = statement.order_by(None)
        for name, reverse in self.effective_orderings:
            column = statement.selected_columns[name]
            statement = statement.order_by(
                column.desc() if reverse else column.asc()
            )
        if not isinstance(self.limit_value, UndefinedType):
            statement = statement.limit(self.limit_value)
        return statement.offset(self.offset_value or None)


def comparison(
    column: ColumnElement[FilterValue], condition: Comparison[FilterValue]
) -> ColumnElement[bool]:
    value = condition.value
    operations: dict[ComparisonKind, Callable[[], ColumnElement[bool]]] = {
        "eq": lambda: column == value,
        "ne": lambda: (
            or_(column != value, column.is_(None))
            if value is not None
            else column.is_not(None)
        ),
        "gt": lambda: column > value,
        "gte": lambda: column >= value,
        "lt": lambda: column < value,
        "lte": lambda: column <= value,
    }
    if value is None and condition.kind not in {"eq", "ne"}:
        return false()
    return operations[condition.kind]()


def membership(
    column: ColumnElement[FilterValue], condition: In[FilterValue]
) -> ColumnElement[bool] | None:
    if not isinstance(condition.values, Sequence):
        return None
    values = tuple(value for value in condition.values if value is not None)
    result = column.in_(values)
    return or_(result, column.is_(None)) if None in condition.values else result


def combine(
    conditions: tuple[ColumnElement[bool] | None, ...], *, conjunction: bool
) -> ColumnElement[bool] | None:
    if any(condition is None for condition in conditions):
        return None
    present = tuple(
        condition for condition in conditions if condition is not None
    )
    return and_(true(), *present) if conjunction else or_(false(), *present)


def negate(condition: ColumnElement[bool] | None) -> ColumnElement[bool] | None:
    return (
        None if condition is None else not_(func.coalesce(condition, false()))
    )


def exclusive(
    conditions: tuple[ColumnElement[bool] | None, ...],
) -> ColumnElement[bool] | None:
    result: ColumnElement[bool] = false()
    for condition in conditions:
        if condition is None:
            return None
        result = result != func.coalesce(condition, false())
    return result


def compile_value(
    column: ColumnElement[FilterValue], condition: Filter[FilterValue]
) -> ColumnElement[bool] | None:
    if isinstance(condition, Not):
        inner = compile_value(column, condition.condition)
        return negate(inner)
    if isinstance(condition, Comparison):
        return comparison(column, condition)
    if isinstance(condition, In):
        return membership(column, condition)
    if isinstance(condition, And | Or):
        children = tuple(
            compile_value(column, child) for child in condition.conditions
        )
        return (
            exclusive(children)
            if isinstance(condition, Xor)
            else combine(children, conjunction=isinstance(condition, And))
        )
    return compile_scalar(column, condition)


def compile_scalar(
    column: ColumnElement[FilterValue], condition: FilterValue
) -> ColumnElement[bool] | None:
    if isinstance(condition, str) and not isinstance(condition, Enum):
        # Python casefold handles Unicode differently from database collations.
        return None
    return column == condition


def compile_predicate[E](
    expression: Expression[E],
    source: type[E],
    column: Callable[[str], ColumnElement[FilterValue]],
) -> ColumnElement[bool] | None:
    if isinstance(expression, Not):
        inner = compile_predicate(expression.condition, source, column)
        return negate(inner)
    if isinstance(expression, Xor):
        return exclusive(
            tuple(
                compile_predicate(child, source, column)
                for child in expression.conditions
            )
        )
    if isinstance(expression, And | Or):
        return combine(
            tuple(
                compile_predicate(child, source, column)
                for child in expression.conditions
            ),
            conjunction=isinstance(expression, And),
        )
    if isinstance(expression, FieldPredicate):
        return compile_field(expression, source, column)
    return None


def compile_field[E](
    expression: FieldPredicate[E],
    source: type[E],
    column: Callable[[str], ColumnElement[FilterValue]],
) -> ColumnElement[bool] | None:
    if expression.source is not source:
        raise TypeError("Filter field must belong to the stream entity")
    return compile_value(column(expression.name), expression.condition)
