"""Execute dependencies with the arguments of the current invocation."""

from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    Callable,
    Sequence,
)
from contextlib import aclosing
from functools import wraps
from inspect import BoundArguments, Signature, signature
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4

from fastsprout.core.types import Chunk
from fastsprout.core.types.iterable import resolve_any_iterable
from fastsprout.core.types.protocols.ables import Hashable

from .bindings import dependency_bindings
from .injector import inject_depends
from .marker import DependsClass
from .scope import async_invocation_scope

__all__ = ["DependencyOwner", "stream_dependencies", "with_dependencies"]


@runtime_checkable
class DependencyOwner(Protocol):
    dependencies: Sequence[DependsClass]


class InvocationBindings:
    def __init__(
        self,
        arguments: BoundArguments,
        operation: str,
    ) -> None:
        self.token = uuid4()
        self.providers: set[Hashable] = set()
        self.cache_keys: set[Hashable] = set()
        self.arguments = arguments
        self.arguments.apply_defaults()
        self.arguments.arguments.setdefault("operation", operation)

    def bind(self, arguments: BoundArguments) -> None:
        inject_depends.bind(arguments, self.arguments)

    def key[**P, R](
        self, signature: Signature, provider: Callable[P, R]
    ) -> UUID | None:
        arguments = signature.bind_partial()
        self.bind(arguments)
        return (
            self.token
            if arguments.arguments or provider in self.providers
            else None
        )

    def replace_chunk[T](
        self, replacement: Chunk[T], bound: BoundArguments
    ) -> None:
        names = [
            name
            for name, value in bound.arguments.items()
            if isinstance(value, Chunk)
        ]
        if len(names) != 1:
            raise TypeError(
                "A Chunk result requires exactly one Chunk argument"
            )
        name = names[0]
        bound.arguments[name] = replacement
        self.arguments.arguments[name] = replacement
        self.token = uuid4()


def with_dependencies[**P, R](
    function: Callable[P, Awaitable[R]],
    dependencies: Sequence[DependsClass] = (),
) -> Callable[P, Awaitable[R]]:
    parameters = signature(function)

    @wraps(function)
    async def call(*args: P.args, **kwargs: P.kwargs) -> R:
        bindings = InvocationBindings(
            parameters.bind_partial(*args, **kwargs), function.__name__
        )
        owner = bindings.arguments.arguments.get("self")
        inherited = (
            owner.dependencies if isinstance(owner, DependencyOwner) else ()
        )
        checks = (*inherited, *dependencies)
        bindings.providers = {
            inject_depends.provider(dependency, None) for dependency in checks
        }
        async with async_invocation_scope():
            with dependency_bindings(bindings):
                bound = await inject_depends.ainject(function, args, kwargs)
                bound.apply_defaults()
                bindings.arguments.arguments.update(bound.arguments)
                for dependency in checks:
                    result = await inject_depends.aresolve(dependency, None)
                    if isinstance(result, Chunk):
                        bindings.replace_chunk(result, bound)
                return await function(*bound.args, **bound.kwargs)

    return call


def stream_dependencies[**P, T](
    function: Callable[P, AsyncIterable[T]],
) -> Callable[P, AsyncGenerator[T, None]]:
    @wraps(function)
    async def source(*args: P.args, **kwargs: P.kwargs) -> AsyncIterable[T]:
        return function(*args, **kwargs)

    run = with_dependencies(source)

    @wraps(function)
    async def iterate(
        *args: P.args, **kwargs: P.kwargs
    ) -> AsyncGenerator[T, None]:
        async with async_invocation_scope():
            async with aclosing(
                resolve_any_iterable(await run(*args, **kwargs))
            ) as iterator:
                async for item in iterator:
                    yield item

    return iterate
