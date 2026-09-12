from typing import Protocol, runtime_checkable

from .ables import AllComparisonsable, Hashable

__all__ = ["Identificatable"]


@runtime_checkable
class Identificatable[T](Hashable, AllComparisonsable[T], Protocol): ...
