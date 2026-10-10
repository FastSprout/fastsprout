"""Execute dependencies with the arguments of the current invocation."""

from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from inspect import BoundArguments, Signature, signature
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4

from .bindings import dependency_bindings
from .injector import inject_depends
from .marker import DependsClass
from .scope import invocation_scope

__all__ = ["DependencyOwner", "with_dependencies"]


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
        self.arguments = arguments
        self.arguments.apply_defaults()
        self.arguments.arguments.setdefault("operation", operation)

    def bind(self, arguments: BoundArguments) -> None:
        inject_depends.bind(arguments, self.arguments)

    def key(self, signature: Signature) -> UUID | None:
        arguments = signature.bind_partial()
        self.bind(arguments)
        return self.token if arguments.arguments else None


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
        with invocation_scope():
            with dependency_bindings(bindings):
                bound = await inject_depends.ainject(function, args, kwargs)
                bound.apply_defaults()
                bindings.arguments.arguments.update(bound.arguments)
                owner = bound.arguments.get("self")
                inherited = (
                    owner.dependencies
                    if isinstance(owner, DependencyOwner)
                    else ()
                )
                for dependency in (*inherited, *dependencies):
                    await inject_depends.aresolve(dependency, None)
                return await function(*bound.args, **bound.kwargs)

    return call
