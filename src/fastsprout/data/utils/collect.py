import inspect
from collections.abc import AsyncIterator, Callable, Coroutine, Sequence
from functools import wraps
from typing import Any, cast

from fastsprout.data.exceptions import NotFoundError

__all__ = ["collect", "collect_first", "collect_one"]


def collect[T, **P](
    func: Callable[P, AsyncIterator[T]],
) -> Callable[P, Coroutine[Any, Any, Sequence[T]]]:
    """Convert an async-generator yielding ``Sequence[T]`` chunks
    into a regular async function returning a flat ``list[T]``."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> list[T]:
        return [x async for x in func(*args, **kwargs)]

    cast(Any, wrapper).__signature__ = inspect.signature(func)
    return cast(Callable[P, Coroutine[Any, Any, list[T]]], wrapper)


def collect_first[T, **P](
    func: Callable[P, AsyncIterator[Sequence[T]]],
) -> Callable[P, Coroutine[Any, Any, T | None]]:
    """Return the first item from the async-generator, or ``None``."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T | None:
        kwargs.setdefault("chunk_size", 1)
        async for chunk in func(*args, **kwargs):
            for item in chunk:
                return item
        return None

    cast(Any, wrapper).__signature__ = inspect.signature(func)
    return cast(Callable[P, Coroutine[Any, Any, T | None]], wrapper)


def collect_one[T, **P](
    func: Callable[P, AsyncIterator[Sequence[T]]],
) -> Callable[P, Coroutine[Any, Any, T]]:
    """Return the first item from the async-generator or raise
    ``NotFoundError`` if there are none."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        kwargs.setdefault("chunk_size", 1)
        async for chunk in func(*args, **kwargs):
            for item in chunk:
                return item
        raise NotFoundError()

    cast(Any, wrapper).__signature__ = inspect.signature(func)
    return cast(Callable[P, Coroutine[Any, Any, T]], wrapper)
