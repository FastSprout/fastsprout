from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from fastsprout.core.types.schema import Schema

__all__ = ["DependencyResolvable"]


@runtime_checkable
class DependencyResolvable(Protocol):
    def resolve[T: Schema](
        self,
        annotation: type[T],
        resolve_provider: Callable[[Callable[..., Schema]], Schema],
    ) -> T: ...

    async def aresolve[T: Schema](
        self,
        annotation: type[T],
        resolve_provider: Callable[[Callable[..., Schema]], Awaitable[Schema]],
    ) -> T: ...
