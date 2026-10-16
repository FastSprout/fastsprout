"""Typed actions and the direct-call execution wrapper."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

from fastsprout.core.depends import DependsClass
from fastsprout.core.depends.invocation import (
    DependencyOwner,
    with_dependencies,
)

__all__ = ["FunctionAction"]


class FunctionAction[**P, R]:
    """Callable object so assignment to a action never binds ``self``."""

    def __init__(
        self,
        function: Callable[P, Awaitable[R]],
        *,
        dependencies: Sequence[DependsClass] = (),
        source: Callable[P, Awaitable[R]] | None = None,
    ) -> None:
        self.dependencies = dependencies
        self.target = function
        self.function = with_dependencies(function, dependencies)
        self.__wrapped__ = function if source is None else source

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return await self.function(*args, **kwargs)

    @property
    def dependency(self) -> DependsClass:
        return DependsClass(self)

    def __get__[Owner](
        self, instance: Owner | None, owner: type[Owner] | None = None
    ) -> FunctionAction[P, R]:
        if isinstance(instance, DependencyOwner) and instance.dependencies:
            return FunctionAction(
                self.target,
                dependencies=(*instance.dependencies, *self.dependencies),
                source=self.__wrapped__,
            )
        return self
