from collections.abc import AsyncGenerator, AsyncIterator, Generator, Iterator
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from contextvars import ContextVar
from typing import Any

__all__ = [
    "async_invocation_scope",
    "current_dependency_cache",
    "dependency_resources",
    "invocation_scope",
    "resolve_yield",
]

dependency_resources: ContextVar[AsyncExitStack | None] = ContextVar(
    "fastsprout_dependency_resources", default=None
)


async def resolve_yield[T](
    value: AsyncGenerator[T, None] | Generator[T, None, None],
) -> T:
    resources = dependency_resources.get()
    if resources is None:
        raise RuntimeError("Yield dependencies require an async invocation")
    if isinstance(value, AsyncGenerator):
        return await resources.enter_async_context(
            asynccontextmanager(lambda: value)()
        )
    return resources.enter_context(contextmanager(lambda: value)())


@asynccontextmanager
async def async_invocation_scope() -> AsyncIterator[None]:
    with invocation_scope():
        if dependency_resources.get() is not None:
            yield
            return
        resources = AsyncExitStack()
        token = dependency_resources.set(resources)
        try:
            async with resources:
                yield
        finally:
            dependency_resources.reset(token)


dependency_cache: ContextVar[dict[object, Any] | None] = ContextVar(
    "fastsprout_invocation_dependencies", default=None
)


@contextmanager
def invocation_scope() -> Iterator[None]:
    if dependency_cache.get() is not None:
        yield
        return
    token = dependency_cache.set({})
    try:
        yield
    finally:
        dependency_cache.reset(token)


def current_dependency_cache() -> dict[object, Any] | None:
    return dependency_cache.get()
