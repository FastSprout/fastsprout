"""Query expression evaluation using the shared field predicates."""

from collections.abc import Awaitable, Callable
from typing import Never

from fastsprout.core.fields.field_predicate import FieldPredicate, matches
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types import FilterValue
from fastsprout.data.types import PredicateCallable
from fastsprout.data.utils.callable import resolve_any_callable

from .operators import And, Comparison, Filter, In, Not, Or, Xor

__all__ = [
    "Expression",
    "FieldPredicate",
    "evaluate",
    "evaluate_filter",
    "matches",
    "where",
]

type Expression[E] = Filter[PredicateCallable[E]]


def where[E, T: FilterValue, Orm](
    field: FieldRef[E, T, Orm], condition: Filter[T]
) -> FieldPredicate[E]:
    return FieldPredicate(field.entity_cls, field.name, condition)


async def evaluate[E](expression: Expression[E], entity: E) -> bool:
    async def check(expression: PredicateCallable[E]) -> bool:
        predicate: Callable[[E], Awaitable[bool]] = resolve_any_callable(
            expression
        )
        return await predicate(entity)

    return await evaluate_filter(expression, check)


async def evaluate_filter[T: Callable[[Never], bool | Awaitable[bool]]](
    expression: Filter[T], check: Callable[[T], Awaitable[bool]]
) -> bool:
    """Share group evaluation while callers resolve each leaf's input."""
    if isinstance(expression, Not):
        return not await evaluate_filter(expression.condition, check)
    if isinstance(expression, And | Or):
        return await evaluate_group(expression, check)
    if isinstance(expression, Comparison | In):
        raise TypeError("Entity filters require field conditions or predicates")
    return await check(expression)


async def evaluate_group[T: Callable[[Never], bool | Awaitable[bool]]](
    expression: And[T] | Or[T], check: Callable[[T], Awaitable[bool]]
) -> bool:
    if isinstance(expression, Xor):
        result = False
        for child in expression.conditions:
            result ^= await evaluate_filter(child, check)
        return result
    conjunction = isinstance(expression, And)
    for child in expression.conditions:
        if await evaluate_filter(child, check) != conjunction:
            return not conjunction
    return conjunction
