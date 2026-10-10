from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

__all__ = [
    "current_dependency_cache",
    "invocation_scope",
]

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
