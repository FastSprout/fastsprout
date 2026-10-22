"""Typed actions and the direct-call execution wrapper."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from inspect import Signature, signature
from types import MethodType
from typing import Concatenate
from weakref import WeakValueDictionary

from fastsprout.core.depends import DependsClass, inject_depends
from fastsprout.core.depends.invocation import (
    DependencyOwnable,
    with_dependencies,
)

__all__ = ["FunctionAction", "GroupFunctionAction", "MethodAction"]


class FunctionAction[**P, R]:
    """Callable object so assignment to an action never binds ``self``."""

    def __init__(
        self,
        function: Callable[P, Awaitable[R]],
        *,
        dependencies: Sequence[DependsClass] = (),
        source: Callable[P, Awaitable[R]] | None = None,
    ) -> None:
        self.dependencies: Sequence[DependsClass] = dependencies
        self.target: Callable[P, Awaitable[R]] = function
        self.function: Callable[P, Awaitable[R]] = with_dependencies(
            function, dependencies
        )
        self.__wrapped__: Callable[P, Awaitable[R]] = (
            function if source is None else source
        )

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return await self.function(*args, **kwargs)

    @property
    def dependency(self) -> DependsClass:
        return DependsClass(self)


class GroupFunctionAction[**P, R](FunctionAction[P, R]):
    def __get__[Owner](
        self, instance: Owner | None, owner: type[Owner] | None = None
    ) -> FunctionAction[P, R]:
        if isinstance(instance, DependencyOwnable) and instance.dependencies:
            return FunctionAction(
                self.target,
                dependencies=(*instance.dependencies, *self.dependencies),
                source=self.__wrapped__,
            )
        return self


class MethodProvider[Owner, **P, R]:
    def __init__(
        self,
        function: Callable[Concatenate[Owner, P], Awaitable[R]],
        owner: type[Owner],
    ) -> None:
        self.function: Callable[Concatenate[Owner, P], Awaitable[R]] = function
        self.owner: type[Owner] = owner
        self.__name__: str = function.__name__
        self.__wrapped__: Callable[Concatenate[Owner, P], Awaitable[R]] = (
            function
        )
        parameters = signature(function)
        self.__signature__: Signature = parameters.replace(
            parameters=tuple(parameters.parameters.values())[1:]
        )

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        instance: Owner = await inject_depends.aresolve(
            DependsClass(self.owner), self.owner
        )
        return await self.function(instance, *args, **kwargs)


class MethodAction[Owner, **P, R](FunctionAction[Concatenate[Owner, P], R]):
    def __init__(
        self,
        function: Callable[Concatenate[Owner, P], Awaitable[R]],
        *,
        dependencies: Sequence[DependsClass] = (),
    ) -> None:
        super().__init__(function, dependencies=dependencies)
        self.providers: dict[type[Owner], FunctionAction[P, R]] = {}
        self.bindings: WeakValueDictionary[MethodType, FunctionAction[P, R]] = (
            WeakValueDictionary()
        )

    def __get__(
        self, instance: Owner | None, owner: type[Owner]
    ) -> FunctionAction[P, R]:
        if instance is not None:
            method = MethodType(self.function, instance)
            bound_action = self.bindings.get(method)
            if bound_action is None:
                bound: Callable[P, Awaitable[R]] = method
                bound_action = FunctionAction(bound)
                self.bindings[method] = bound_action
            return bound_action
        if owner not in self.providers:
            self.providers[owner] = FunctionAction(
                MethodProvider(self.function, owner)
            )
        return self.providers[owner]
