"""Values that follow nested action calls within one invocation."""

import asyncio
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any

from fastsprout.core.depends import DependsClass, inject_depends
from fastsprout.core.depends.scope import current_dependency_cache
from fastsprout.core.types.schema import Schema

__all__ = [
    "Context",
    "ContextClass",
    "aresolve_context",
    "current_context",
    "resolve_context",
]


class ContextClass:
    def __init__(self, provider: Callable[..., Schema] | None = None) -> None:
        self.provider = provider

    def resolve[T: Schema](
        self,
        annotation: type[T],
        resolve_provider: Callable[[Callable[..., Schema]], Schema],
    ) -> T:
        return resolve_context(self, annotation, resolve_provider)

    async def aresolve[T: Schema](
        self,
        annotation: type[T],
        resolve_provider: Callable[[Callable[..., Schema]], Awaitable[Schema]],
    ) -> T:
        return await aresolve_context(self, annotation, resolve_provider)


resolving_providers: ContextVar[frozenset[type[Schema]]] = ContextVar(
    "fastsprout_context_providers", default=frozenset()
)


def Context(  # noqa: N802  # Context follows the public Depends marker naming.
    provider: Callable[..., Schema] | None = None,
) -> Any:
    """Request a typed value from the current invocation or its provider."""
    return ContextClass(provider)


def context_values() -> dict[type[Schema], Schema]:
    return {}


def current_context() -> dict[type[Schema], Schema]:
    if current_dependency_cache() is None:
        raise RuntimeError("Context() requires an action invocation")
    return inject_depends.resolve(DependsClass(context_values), None)


def context_value[T: Schema](annotation: type[T], value: Schema) -> T:
    if not isinstance(value, annotation):
        raise TypeError(f"Context provider must return {annotation.__name__}")
    return value


def resolve_context[T: Schema](
    marker: ContextClass,
    annotation: type[T],
    resolve_provider: Callable[[Callable[..., Schema]], Schema],
) -> T:
    values = current_context()
    if annotation in values:
        return context_value(annotation, values[annotation])
    if marker.provider is None:
        raise LookupError(f"No context value for {annotation}")
    value = context_value(annotation, resolve_provider(marker.provider))
    values[annotation] = value
    return value


async def aresolve_context[T: Schema](
    marker: ContextClass,
    annotation: type[T],
    resolve_provider: Callable[[Callable[..., Schema]], Awaitable[Schema]],
) -> T:
    values = current_context()
    if annotation in values:
        return context_value(annotation, values[annotation])
    cache = current_dependency_cache()
    if cache is None:
        raise RuntimeError("Context() requires an action invocation")
    if annotation in resolving_providers.get():
        raise RuntimeError(f"Circular context dependency: {annotation}")
    lock: asyncio.Lock = cache.setdefault(
        (aresolve_context, annotation), asyncio.Lock()
    )
    async with lock:
        return await aresolve_context_value(
            marker, annotation, resolve_provider
        )


async def aresolve_context_value[T: Schema](
    marker: ContextClass,
    annotation: type[T],
    resolve_provider: Callable[[Callable[..., Schema]], Awaitable[Schema]],
) -> T:
    values = current_context()
    if annotation in values:
        return context_value(annotation, values[annotation])
    if marker.provider is None:
        raise LookupError(f"No context value for {annotation}")
    token = resolving_providers.set(resolving_providers.get() | {annotation})
    try:
        value = context_value(
            annotation, await resolve_provider(marker.provider)
        )
        values[annotation] = value
        return value
    finally:
        resolving_providers.reset(token)
