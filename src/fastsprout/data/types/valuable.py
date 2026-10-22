from typing import Protocol, Self

from fastsprout.core.types import ables

__all__ = ["HashableAndValuable", "Valuable"]


class Valuable(
    ables.Addable["Valuable", "Valuable"],
    ables.AllComparisonsable["Valuable"],
    Protocol,
):
    def __add__(self, x: Self, /) -> "Valuable": ...

    def __lt__(self, other: Self, /) -> ables.Boolable: ...

    def __le__(self, other: Self, /) -> ables.Boolable: ...

    def __gt__(self, other: Self, /) -> ables.Boolable: ...

    def __ge__(self, other: Self, /) -> ables.Boolable: ...


class HashableAndValuable(ables.Hashable, Valuable, Protocol): ...
