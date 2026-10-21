from types import CodeType
from typing import Protocol

from .protocols.ables import Awaitable, Callable

__all__ = [
    "AnyCallable",
    "AnyCallableEmpty",
    "AsyncFunctionable",
    "AsyncMethodable",
]


type AnyCallable[S, R] = Callable[[S], R] | Callable[[S], Awaitable[R]]
type AnyCallableEmpty[R] = Callable[[], R] | Callable[[], Awaitable[R]]


class AsyncFunctionable[**P, R](Protocol):
    """Distinguish async functions from callable class constructors in overloads."""

    @property
    def __code__(self) -> CodeType: ...

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Awaitable[R]: ...


class AsyncMethodable[Owner, **P, R](Protocol):
    """Recognize the named ``self`` parameter without treating aliases as methods."""

    @property
    def __code__(self) -> CodeType: ...

    # Class binding leaves the callable's own ``self`` parameter in its signature.
    @classmethod
    def __call__(
        cls, self: Owner, *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[R]: ...
