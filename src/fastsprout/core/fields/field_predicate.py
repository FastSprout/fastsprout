"""Callable field conditions shared by queries and in-memory streams."""

from collections.abc import Callable, Sequence
from enum import Enum
from operator import ge, gt, le, lt
from typing import Final

from fastsprout.core.types.comparable import FilterValue, OrderedValue
from fastsprout.core.types.protocols.ables import Boolable

from .conditions import (
    And,
    Comparison,
    ComparisonKind,
    Filter,
    In,
    Not,
    Or,
    Xor,
)

__all__ = ["FieldPredicate", "matches"]

COMPARISONS: dict[
    ComparisonKind, Callable[[OrderedValue, OrderedValue], Boolable]
] = {"gt": gt, "gte": ge, "lt": lt, "lte": le}


def compare(value: FilterValue, condition: Comparison[FilterValue]) -> bool:
    if condition.kind in {"eq", "ne"}:
        equal = bool(value == condition.value)
        return equal if condition.kind == "eq" else not equal
    left = value.value if isinstance(value, Enum) else value
    right = (
        condition.value.value
        if isinstance(condition.value, Enum)
        else condition.value
    )
    return (
        left is not None
        and right is not None
        and bool(COMPARISONS[condition.kind](left, right))
    )


async def matches(value: FilterValue, condition: Filter[FilterValue]) -> bool:
    if isinstance(condition, Not):
        return not await matches(value, condition.condition)
    if isinstance(condition, Comparison):
        return compare(value, condition)
    if isinstance(condition, In):
        values = (
            condition.values
            if isinstance(condition.values, Sequence)
            else await condition.resolved
        )
        return value in values
    if isinstance(condition, And | Or):
        return await match_group(value, condition)
    return match_value(value, condition)


async def match_group(
    value: FilterValue, condition: And[FilterValue] | Or[FilterValue]
) -> bool:
    if isinstance(condition, Xor):
        result = False
        for child in condition.conditions:
            result ^= await matches(value, child)
        return result
    conjunction = isinstance(condition, And)
    for child in condition.conditions:
        if await matches(value, child) != conjunction:
            return not conjunction
    return conjunction


def match_value(value: FilterValue, condition: FilterValue) -> bool:
    if isinstance(condition, str) and not isinstance(condition, Enum):
        return (
            isinstance(value, str) and condition.casefold() in value.casefold()
        )
    return bool(value == condition)


class FieldPredicate[E]:
    def __init__(
        self, source: type[E], name: str, condition: Filter[FilterValue]
    ) -> None:
        self.source: Final[type[E]] = source
        self.name: Final[str] = name
        self.condition: Final[Filter[FilterValue]] = condition

    async def __call__(self, entity: E) -> bool:
        return await matches(getattr(entity, self.name), self.condition)
