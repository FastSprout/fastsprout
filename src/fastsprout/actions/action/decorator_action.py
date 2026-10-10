"""Decorate ordinary async functions and callable action groups."""

import inspect
from collections.abc import Awaitable, Callable, Sequence
from typing import Self, get_type_hints, overload

from fastsprout.core.depends import DependsClass, inject_depends
from fastsprout.core.depends.invocation import with_dependencies
from fastsprout.core.types import AsyncFunction

from .function_action import FunctionAction

__all__ = ["action", "decorate_action_group"]


class ActionGroupDependency[T]:
    def __init__(self, marker: DependsClass, annotation: type[T]) -> None:
        self.marker = marker
        self.annotation = annotation

    @overload
    def __get__[Owner](self, instance: None, owner: type[Owner]) -> Self: ...

    @overload
    def __get__[Owner](self, instance: Owner, owner: type[Owner]) -> T: ...

    def __get__[Owner](
        self, instance: Owner | None, owner: type[Owner]
    ) -> Self | T:
        if instance is None:
            return self
        return inject_depends.resolve(self.marker, self.annotation)


def decorate_action_group[T](action_group: type[T]) -> type[T]:
    type.__setattr__(action_group, "__action_group__", True)
    annotations = get_type_hints(action_group)
    for name, member in vars(action_group).items():
        if isinstance(member, DependsClass):
            setattr(
                action_group,
                name,
                ActionGroupDependency(member, annotations[name]),
            )
            continue
        if name.startswith("_") or not inspect.iscoroutinefunction(member):
            continue
        first = next(iter(inspect.signature(member).parameters), None)
        wrapped = (
            with_dependencies(member)
            if first == "self" and not inspect.ismethod(member)
            else FunctionAction(member)
        )
        setattr(action_group, name, wrapped)
    return action_group


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
            return decorate_action_group(target)
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
    """Make a function or action_group participate in direct-call dependency injection."""
    decorator = ActionDecorator(dependencies)
    return decorator if target is None else decorator(target)
