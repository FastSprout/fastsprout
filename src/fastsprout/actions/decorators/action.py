"""Decorate ordinary async functions and callable action groups."""

import inspect
from collections.abc import Awaitable, Callable, Sequence
from typing import overload

from fastsprout.core.depends import DependsClass
from fastsprout.core.types import AsyncFunction

from ..action import FunctionAction
from ..service import decorate_service

__all__ = ["action"]


class ActionDecorator:
    def __init__(self, dependencies: Sequence[DependsClass]) -> None:
        self.dependencies = dependencies

    @overload
    def __call__[T](self, target: type[T]) -> type[T]: ...

    @overload
    def __call__[**P, R](
        self, target: AsyncFunction[P, R]
    ) -> FunctionAction[P, R]: ...

    def __call__[T, **P, R](
        self, target: type[T] | Callable[P, Awaitable[R]]
    ) -> type[T] | FunctionAction[P, R]:
        if isinstance(target, type):
            if self.dependencies:
                type.__setattr__(target, "dependencies", self.dependencies)
            return decorate_service(target)
        if not inspect.iscoroutinefunction(target):
            raise TypeError("@action requires an async function or class")
        return FunctionAction(target, dependencies=self.dependencies)


@overload
def action(*, dependencies: Sequence[DependsClass] = ()) -> ActionDecorator: ...


@overload
def action[T](
    target: type[T], *, dependencies: Sequence[DependsClass] = ()
) -> type[T]: ...


@overload
def action[**P, R](
    target: AsyncFunction[P, R],
    *,
    dependencies: Sequence[DependsClass] = (),
) -> FunctionAction[P, R]: ...


def action[T, **P, R](
    target: type[T] | Callable[P, Awaitable[R]] | None = None,
    *,
    dependencies: Sequence[DependsClass] = (),
) -> type[T] | FunctionAction[P, R] | ActionDecorator:
    """Make a function or service participate in direct-call dependency injection."""
    decorator = ActionDecorator(dependencies)
    return decorator if target is None else decorator(target)
