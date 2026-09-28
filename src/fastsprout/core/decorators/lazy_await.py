from collections.abc import (
    Awaitable,
    Callable,
)
from functools import wraps
from typing import cast

from fastsprout.core.types import LazyAwait

__all__ = ["hidden_lazy_await", "lazy_await"]


def lazy_await[**P, R](
    method: Callable[P, Awaitable[R]],
) -> Callable[P, LazyAwait[R]]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> LazyAwait[R]:
        return LazyAwait(lambda: method(*args, **kwargs))

    return wrapper


def hidden_lazy_await[**P, R](
    method: Callable[P, Awaitable[R]],
) -> Callable[P, R]:
    lazy_wrapped = lazy_await(method)

    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return cast(R, lazy_wrapped(*args, **kwargs))

    return wrapper
