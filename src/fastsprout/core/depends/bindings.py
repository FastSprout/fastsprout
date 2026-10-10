"""Optional argument bindings for nested dependency resolution."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from inspect import BoundArguments, Signature
from typing import Protocol
from uuid import UUID

__all__ = [
    "DependencyBindings",
    "bind_arguments",
    "dependency_bindings",
    "dependency_key",
    "enter_provider",
]


class DependencyBindings(Protocol):
    def bind(self, arguments: BoundArguments) -> None: ...

    def key(self, signature: Signature) -> UUID | None: ...


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


def bind_arguments(arguments: BoundArguments) -> None:
    bindings = current_bindings.get()
    if bindings is not None:
        bindings.bind(arguments)


def dependency_key(signature: Signature) -> UUID | None:
    bindings = current_bindings.get()
    return None if bindings is None else bindings.key(signature)


def enter_provider[Provider](provider: Provider, active: set[Provider]) -> None:
    if provider in active:
        raise RuntimeError(f"Circular dependency: {provider}")
    active.add(provider)
