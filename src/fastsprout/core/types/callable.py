from .protocols.ables import Awaitable, Callable

__all__ = ["AnyCallable", "AnyCallableEmpty"]


type AnyCallable[S, R] = Callable[[S], R] | Callable[[S], Awaitable[R]]
type AnyCallableEmpty[R] = Callable[[], R] | Callable[[], Awaitable[R]]
