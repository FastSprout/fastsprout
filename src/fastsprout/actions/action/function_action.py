"""Typed actions and the direct-call execution wrapper."""

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
