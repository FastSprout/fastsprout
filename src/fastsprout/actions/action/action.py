"""Typed actions and the direct-call execution wrapper."""

from collections.abc import Awaitable, Callable, Sequence

from fastsprout.core.action import BaseAction
from fastsprout.core.depends import DependsClass
from fastsprout.core.depends.invocation import (
    DependencyOwner,
    with_dependencies,
)
from fastsprout.core.types.schema import Schema

__all__ = ["Action", "FunctionAction"]


class Action[I: Schema, O: Schema](BaseAction[I, O]):
    """Base for a class action with one typed input and output."""

    dependencies: Sequence[DependsClass] = ()

    def __init__(
        self, *, dependencies: Sequence[DependsClass] | None = None
    ) -> None:
        if dependencies is not None:
            self.dependencies = dependencies

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        method = cls.__dict__.get("__call__")
        if method is not None:
            type.__setattr__(cls, "__call__", with_dependencies(method))


class FunctionAction[**P, R]:
    """Callable object so assignment to a service never binds ``self``."""

    def __init__(
        self,
        function: Callable[P, Awaitable[R]],
        *,
        dependencies: Sequence[DependsClass] = (),
    ) -> None:
        self.dependencies = dependencies
        self.function = with_dependencies(function, dependencies)
        self.__wrapped__ = function

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return await self.function(*args, **kwargs)

    def __get__[Owner](
        self, instance: Owner | None, owner: type[Owner] | None = None
    ) -> Callable[P, Awaitable[R]]:
        if isinstance(instance, DependencyOwner) and instance.dependencies:
            return with_dependencies(
                self.__wrapped__,
                dependencies=(*instance.dependencies, *self.dependencies),
            )
        return self
