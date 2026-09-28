from fastsprout.core.types import AnyCallable, ables

__all__ = [
    "ConsumerCallable",
    "MapperCallable",
    "PredicateCallable",
    "ReducerCallable",
]


type MapperCallable[S, R] = AnyCallable[S, R]
type PredicateCallable[S] = AnyCallable[S, bool]
type GetterCallable[S, R] = AnyCallable[S, R]

type ConsumerCallable[S] = AnyCallable[S, None]
type ReducerCallable[S, R] = (
    ables.Callable[[S, R], R] | ables.Callable[[S, R], ables.Awaitable[R]]
)
