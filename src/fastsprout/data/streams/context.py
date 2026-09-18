from collections.abc import AsyncGenerator
from contextlib import aclosing
from contextvars import ContextVar
from dataclasses import dataclass

from fastsprout.data.exceptions import MixedStreamContextsError, NoSessionError


class StreamContext:
    """Identity and lifetime of one router context, shared by its sources."""

    def __init__(self) -> None:
        self._active = True

    def close(self) -> None:
        self._active = False

    def check(self) -> None:
        if not self._active:
            raise NoSessionError(
                "The stream's DataR context is no longer active"
            )
        scope = _current_join.get()
        if scope is None:
            return
        if scope.context is None:
            scope.context = self
        elif scope.context is not self:
            raise MixedStreamContextsError(
                "Joined streams must use the same DataR context"
            )


@dataclass
class _JoinScope:
    context: StreamContext | None = None


_current_join: ContextVar[_JoinScope | None] = ContextVar(
    "fastsprout_join_scope", default=None
)


async def in_join_context[T](
    source: AsyncGenerator[T, None],
) -> AsyncGenerator[T, None]:
    """Share ownership checks upstream without leaking state across yields."""
    scope = _current_join.get() or _JoinScope()
    async with aclosing(source):
        while True:
            token = _current_join.set(scope)
            try:
                if scope.context is not None:
                    scope.context.check()
                item = await anext(source)
            except StopAsyncIteration:
                return
            finally:
                _current_join.reset(token)
            yield item
