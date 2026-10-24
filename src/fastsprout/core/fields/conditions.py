"""Backend-independent values used by field conditions."""

from asyncio import Task, create_task
from functools import cached_property
from typing import ClassVar, Final, Literal

from fastsprout.core.types.iterable import AnyIterable, resolve_any_iterable

__all__ = [
    "And",
    "Between",
    "Comparison",
    "ComparisonKind",
    "Eq",
    "Filter",
    "Gt",
    "Gte",
    "In",
    "Lt",
    "Lte",
    "Nand",
    "Ne",
    "Not",
    "NotIn",
    "Or",
    "Xor",
]

type ComparisonKind = Literal["eq", "ne", "gt", "gte", "lt", "lte"]
type Filter[T] = T | Comparison[T] | In[T] | And[T] | Or[T] | Not[T]


class Comparison[T]:
    kind: ClassVar[ComparisonKind] = "eq"

    def __init__(self, value: T) -> None:
        self.value: Final[T] = value


class Eq[T](Comparison[T]):
    kind: ClassVar[ComparisonKind] = "eq"


class Ne[T](Comparison[T]):
    kind: ClassVar[ComparisonKind] = "ne"


class Gt[T](Comparison[T]):
    kind: ClassVar[ComparisonKind] = "gt"


class Gte[T](Comparison[T]):
    kind: ClassVar[ComparisonKind] = "gte"


class Lt[T](Comparison[T]):
    kind: ClassVar[ComparisonKind] = "lt"


class Lte[T](Comparison[T]):
    kind: ClassVar[ComparisonKind] = "lte"


class In[T]:
    def __init__(self, values: AnyIterable[T]) -> None:
        self.values: Final[AnyIterable[T]] = values

    @cached_property
    def resolved(self) -> Task[tuple[T, ...]]:
        return create_task(self.collect())

    async def collect(self) -> tuple[T, ...]:
        return tuple(
            [value async for value in resolve_any_iterable(self.values)]
        )


class And[T]:
    def __init__(self, *conditions: Filter[T]) -> None:
        self.conditions: Final[tuple[Filter[T], ...]] = conditions


class Or[T]:
    def __init__(self, *conditions: Filter[T]) -> None:
        self.conditions: Final[tuple[Filter[T], ...]] = conditions


class Not[T]:
    def __init__(self, condition: Filter[T]) -> None:
        self.condition: Final[Filter[T]] = condition


class Xor[T](Or[T]):
    """Match when an odd number of conditions match."""


class Nand[T](Not[T]):
    def __init__(self, *conditions: Filter[T]) -> None:
        super().__init__(And(*conditions))


class NotIn[T](Not[T]):
    def __init__(self, values: AnyIterable[T]) -> None:
        super().__init__(In(values))


class Between[T](And[T]):
    def __init__(self, lower: T, upper: T) -> None:
        super().__init__(Gte(lower), Lte(upper))
