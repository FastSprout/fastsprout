from collections.abc import AsyncGenerator
from contextlib import aclosing
from contextvars import ContextVar

from fastsprout.core import dataclass
from fastsprout.data.exceptions import MixedStreamContextsError, NoSessionError

__all__ = ["StreamContext", "in_join_context"]


class StreamContext:
    """Identity and lifetime of one router context, shared by its sources."""

    def __init__(self) -> None:
        self.active: bool = True

    def close(self) -> None:
        self.active = False

    def check(self) -> None:
        if not self.active:
            raise NoSessionError(
                "The stream's DataR context is no longer active"
            )
        scope = current_join.get()
        if scope is None:
            return
        if scope.context is None:
            scope.context = self
        elif scope.context is not self:
            raise MixedStreamContextsError(
                "Joined streams must use the same DataR context"
            )


@dataclass
class JoinScope:
    context: StreamContext | None = None


current_join: ContextVar[JoinScope | None] = ContextVar(
    "fastsprout_join_scope", default=None
)


async def in_join_context[T](
    source: AsyncGenerator[T, None],
) -> AsyncGenerator[T, None]:
    """Share ownership checks upstream without leaking state across yields."""
    scope = current_join.get() or JoinScope()
    async with aclosing(source):
        while True:
            token = current_join.set(scope)
            try:
                if scope.context is not None:
                    scope.context.check()
                item = await anext(source)
            except StopAsyncIteration:
                return
            finally:
                current_join.reset(token)
            yield item
