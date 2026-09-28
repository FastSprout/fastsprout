from typing import Protocol

from fastsprout.core.types import ables

__all__ = ["HashableAndValuable", "Valuable"]


class Valuable(ables.Addable, ables.AllComparisonsable, Protocol): ...


class HashableAndValuable(Valuable, ables.Hashable, Protocol): ...
