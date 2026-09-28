from collections.abc import Generator as Generatorable
from typing import Any, Protocol

__all__ = [
    "AIterable",
    "ANextable",
    "Addable",
    "AllComparisonsable",
    "Awaitable",
    "Boolable",
    "Callable",
    "Containsable",
    "DivModable",
    "DunderGEable",
    "DunderGTable",
    "DunderLEable",
    "DunderLTable",
    "Floatable",
    "Generatorable",
    "Hashable",
    "Iterable",
    "Lenable",
    "LenableAndGetItemable",
    "Modable",
    "Mulable",
    "Nextable",
    "RAddable",
    "RDivModable",
    "RModable",
    "RMulable",
    "RSubable",
    "RichComparisonable",
    "Subable",
    "Truncable",
]


class Awaitable[T](Protocol):
    def __await__(self) -> Generatorable[Any, Any, T]: ...


class Nextable[T](Protocol):
    def __next__(self) -> T: ...


class ANextable[T](Protocol):
    def __anext__(self) -> Awaitable[T]: ...


class AIterator[T](ANextable[T], Protocol):
    def __aiter__(self) -> "AIterator[T]": ...


class AIterable[T](Protocol):
    def __aiter__(self) -> AIterator[T]: ...


class Iterator[T](Nextable[T], Protocol):
    def __iter__(self) -> "Iterator[T]": ...


class Iterable[T](Protocol):
    def __iter__(self) -> Iterator[T]: ...


class Callable[**P, R](Protocol):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...


class Boolable(Protocol):
    def __bool__(self) -> bool: ...


class DunderLTable[T](Protocol):
    def __lt__(self, other: T, /) -> Boolable: ...


class DunderGTable[T](Protocol):
    def __gt__(self, other: T, /) -> Boolable: ...


class DunderLEable[T](Protocol):
    def __le__(self, other: T, /) -> Boolable: ...


class DunderGEable[T](Protocol):
    def __ge__(self, other: T, /) -> Boolable: ...


class Eqable[T](Protocol):  # type: ignore
    def __eq__(self, other: T | object, /) -> Boolable: ...  # type: ignore


class Containsable[T](Protocol):
    def __contains__(self, x: T, /) -> Boolable: ...


class AllComparisonsable[T](
    DunderLTable[T],
    DunderGTable[T],
    DunderLEable[T],
    DunderGEable[T],
    Eqable[T],
    Protocol,
): ...


type RichComparisonable[T] = DunderLTable[T] | DunderGTable[T]


class Addable[T, R](Protocol):
    def __add__(self, x: T, /) -> R: ...


class RAddable[T, R](Protocol):
    def __radd__(self, x: T, /) -> R: ...


class Subable[T, R](Protocol):
    def __sub__(self, x: T, /) -> R: ...


class RSubable[T, R](Protocol):
    def __rsub__(self, x: T, /) -> R: ...


class Mulable[T, R](Protocol):
    def __mul__(self, x: T, /) -> R: ...


class RMulable[T, R](Protocol):
    def __rmul__(self, x: T, /) -> R: ...


class Modable[T, R](Protocol):
    def __mod__(self, other: T, /) -> R: ...


class RModable[T, R](Protocol):
    def __rmod__(self, other: T, /) -> R: ...


class DivModable[T, R](Protocol):
    def __divmod__(self, other: T, /) -> R: ...


class RDivModable[T, R](Protocol):
    def __rdivmod__(self, other: T, /) -> R: ...


class Lenable(Protocol):
    def __len__(self) -> int: ...


class LenableAndGetItemable[T](Protocol):
    def __len__(self) -> int: ...
    def __getitem__(self, k: int, /) -> T: ...


class Truncable(Protocol):
    def __trunc__(self) -> int: ...


class Hashable(Protocol):
    def __hash__(self) -> int: ...


class Floatable(Protocol):
    def __float__(self) -> float: ...
