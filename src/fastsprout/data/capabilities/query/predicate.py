"""Query expression evaluation using the shared field predicates."""

from collections.abc import Awaitable, Callable

from fastsprout.core.fields.field_predicate import FieldPredicate, matches
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types import FilterValue
from fastsprout.data.types import PredicateCallable
from fastsprout.data.utils.callable import resolve_any_callable

from .operators import And, Filter, Not, Or, Xor

__all__ = ["Expression", "FieldPredicate", "evaluate", "matches", "where"]

type Expression[E] = Filter[PredicateCallable[E]]


def where[E, T: FilterValue, Orm](
    field: FieldRef[E, T, Orm], condition: Filter[T]
) -> FieldPredicate[E]:
    return FieldPredicate(field.entity_cls, field.name, condition)


async def evaluate[E](expression: Expression[E], entity: E) -> bool:
    if isinstance(expression, Not):
        return not await evaluate(expression.condition, entity)
    if isinstance(expression, And | Or):
        return await evaluate_group(expression, entity)
    if callable(expression):
        predicate: Callable[[E], Awaitable[bool]] = resolve_any_callable(
            expression
        )
        return await predicate(entity)
    raise TypeError("Entity filters require field conditions or predicates")


async def evaluate_group[E](
    expression: And[PredicateCallable[E]] | Or[PredicateCallable[E]], entity: E
) -> bool:
    if isinstance(expression, Xor):
        result = False
        for child in expression.conditions:
            result ^= await evaluate(child, entity)
        return result
    conjunction = isinstance(expression, And)
    for child in expression.conditions:
        if await evaluate(child, entity) != conjunction:
            return not conjunction
    return conjunction
