"""Optional argument bindings for nested dependency resolution."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from inspect import BoundArguments, Signature
from typing import Protocol
from uuid import UUID

from fastsprout.core.types.protocols.ables import Hashable

from .scope import current_dependency_cache

__all__ = [
    "DependencyBindings",
    "bind_arguments",
    "cache_key",
    "dependency_bindings",
    "dependency_key",
    "enter_provider",
]


class DependencyBindings(Protocol):
    cache_keys: set[Hashable]

    def bind(self, arguments: BoundArguments) -> None: ...

    def key[**P, R](
        self, signature: Signature, provider: Callable[P, R]
    ) -> UUID | None: ...


current_bindings: ContextVar[DependencyBindings | None] = ContextVar(
    "fastsprout_dependency_bindings", default=None
)


@contextmanager
def dependency_bindings(bindings: DependencyBindings) -> Iterator[None]:
    token = current_bindings.set(bindings)
    try:
        yield
    finally:
        current_bindings.reset(token)
        cache = current_dependency_cache()
        if cache is not None:
            for key in bindings.cache_keys:
                cache.pop(key, None)


def cache_key[Injector: Hashable, Provider: Hashable](
    injector: Injector, provider: Provider, token: UUID | None
) -> tuple[Injector, Provider, UUID | None]:
    key = (injector, provider, token)
    bindings = current_bindings.get()
    if token is not None and bindings is not None:
        bindings.cache_keys.update((key, (key, "lock")))
    return key


def bind_arguments(arguments: BoundArguments) -> None:
    bindings = current_bindings.get()
    if bindings is not None:
        bindings.bind(arguments)


def dependency_key[**P, R](
    signature: Signature, provider: Callable[P, R]
) -> UUID | None:
    bindings = current_bindings.get()
    return None if bindings is None else bindings.key(signature, provider)


def enter_provider[Provider](provider: Provider, active: set[Provider]) -> None:
    if provider in active:
        raise RuntimeError(f"Circular dependency: {provider}")
    active.add(provider)
