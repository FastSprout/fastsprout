import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from inspect import iscoroutinefunction
from typing import cast, overload

from fastsprout.core.types.callable import AnyCallable
from fastsprout.data.types import ReducerCallable

__all__ = ["resolve_any_callable", "resolve_callable_to_sync"]


@overload
def resolve_any_callable[S, R](
    callable: AnyCallable[S, R],
) -> Callable[[S], Awaitable[R]]: ...


@overload
def resolve_any_callable[S, R](
    callable: ReducerCallable[S, R],
) -> Callable[[S, R], Awaitable[R]]: ...


def resolve_any_callable(callable):
    if iscoroutinefunction(callable):
        return callable

    @wraps(callable)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(callable, *args, **kwargs)  # type: ignore[arg-type]

    return wrapper


def resolve_callable_to_sync[**S, R](
    callable: Callable[S, Awaitable[R]],
    loop: asyncio.AbstractEventLoop | None = None,
) -> Callable[S, R]:
    if not iscoroutinefunction(callable):
        return cast(Callable[S, R], callable)

    @wraps(callable)
    def sync_call(*args, **kwargs):
        try:
            local_loop = loop or asyncio.get_event_loop()
            asyncio.set_event_loop(local_loop)
            if local_loop.is_running():
                return local_loop.run_in_executor(
                    None, callable, *args, **kwargs
                )
            raise RuntimeError
        except RuntimeError:
            return asyncio.run(callable(*args, **kwargs))

    return cast(Callable[S, R], sync_call)
