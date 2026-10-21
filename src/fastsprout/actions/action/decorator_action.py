"""Decorate ordinary async functions and callable action groups."""

import inspect
from collections.abc import Awaitable, Callable, Sequence
from types import MethodType
from typing import Self, TypeGuard, get_type_hints, overload

from fastsprout.core.depends import DependsClass, inject_depends
from fastsprout.core.types import AsyncFunctionable, AsyncMethodable
from fastsprout.core.types.schema import Schema

from .class_action import Action
from .function_action import FunctionAction, GroupFunctionAction, MethodAction

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


def group_action[I: Schema, O: Schema, **P, R](
    member: Action[I, O] | FunctionAction[P, R],
) -> Callable[[I], Awaitable[O]] | FunctionAction[P, R]:
    if isinstance(member, MethodAction):
        return member
    if isinstance(member, FunctionAction):
        return GroupFunctionAction(
            member.target,
            dependencies=member.dependencies,
            source=member.__wrapped__,
        )
    function = inspect.unwrap(member.__call__, stop=inspect.isfunction)
    return GroupFunctionAction(
        MethodType(function, member),
        dependencies=member.dependencies,
        source=member,
    )


def decorate_action_group[T](action_group: type[T]) -> type[T]:
    type.__setattr__(action_group, "__action_group__", True)
    annotations = get_type_hints(action_group)
    for name, member in vars(action_group).items():
        if isinstance(member, Action | FunctionAction):
            setattr(action_group, name, group_action(member))
            continue
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
            MethodAction(member)
            if first == "self" and not inspect.ismethod(member)
            else GroupFunctionAction(member)
        )
        setattr(action_group, name, wrapped)
    return action_group


class ActionDecorator:
    def __init__(self, dependencies: Sequence[DependsClass]) -> None:
        self.dependencies = dependencies

    @overload
    def __call__[T](self, target: type[T]) -> type[T]: ...

    @overload
    def __call__[Owner, **P, R](
        self, target: AsyncMethodable[Owner, P, R]
    ) -> MethodAction[Owner, P, R]: ...

    @overload
    def __call__[**P, R](
        self, target: AsyncFunctionable[P, R]
    ) -> FunctionAction[P, R]: ...

    def __call__[T, Owner, **P, R](
        self,
        target: type[T]
        | AsyncMethodable[Owner, P, R]
        | Callable[P, Awaitable[R]],
    ) -> type[T] | MethodAction[Owner, P, R] | FunctionAction[P, R]:
        if isinstance(target, type):
            if self.dependencies:
                type.__setattr__(target, "dependencies", self.dependencies)
            return decorate_action_group(target)
        return self.function(target)

    def function[Owner, **P, R](
        self,
        target: AsyncMethodable[Owner, P, R] | Callable[P, Awaitable[R]],
    ) -> MethodAction[Owner, P, R] | FunctionAction[P, R]:
        def is_method(
            candidate: AsyncMethodable[Owner, P, R] | Callable[P, Awaitable[R]],
        ) -> TypeGuard[AsyncMethodable[Owner, P, R]]:
            return (
                inspect.iscoroutinefunction(candidate)
                and next(iter(inspect.signature(candidate).parameters), None)
                == "self"
            )

        if is_method(target):
            return MethodAction(target, dependencies=self.dependencies)
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
def action[Owner, **P, R](
    target: AsyncMethodable[Owner, P, R],
    *,
    dependencies: Sequence[DependsClass] = (),
) -> MethodAction[Owner, P, R]: ...


@overload
def action[**P, R](
    target: AsyncFunctionable[P, R],
    *,
    dependencies: Sequence[DependsClass] = (),
) -> FunctionAction[P, R]: ...


def action[T, Owner, **P, R](
    target: type[T]
    | AsyncMethodable[Owner, P, R]
    | Callable[P, Awaitable[R]]
    | None = None,
    *,
    dependencies: Sequence[DependsClass] = (),
) -> (
    type[T] | MethodAction[Owner, P, R] | FunctionAction[P, R] | ActionDecorator
):
    """Make a function or action_group participate in direct-call dependency injection."""
    decorator = ActionDecorator(dependencies)
    return decorator if target is None else decorator(target)
