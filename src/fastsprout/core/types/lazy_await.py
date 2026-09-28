import inspect
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
)
from typing import cast

__all__ = ["LazyAwait"]

_MISSING_VALUE = object()


class LazyAwait[R]:
    __slots__ = ("_callable", "_callable_result")

    def __init__(self, callable: Callable[[], Awaitable[R]]) -> None:
        self._callable = callable
        self._callable_result: R = _MISSING_VALUE  # type: ignore

    async def _resolve(self) -> R:
        if self._callable_result is _MISSING_VALUE:
            pending = self._callable()
            if inspect.isasyncgen(pending):
                self._callable_result = cast(R, pending)
            else:
                self._callable_result = await pending
        return cast(R, self._callable_result)

    def __getattr__(self, name: str) -> Callable[..., "LazyAwait"]:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)

        def call(*args, **kwargs) -> LazyAwait:
            async def step():
                target = await self._resolve()
                result = getattr(target, name)(*args, **kwargs)
                if isinstance(result, LazyAwait) or inspect.isawaitable(result):
                    return await result
                return result

            return LazyAwait(step)

        return call

    def __await__(self):
        return self._resolve().__await__()

    async def __aiter__(self) -> AsyncIterator:
        target = await self._resolve()
        async for item in cast(AsyncIterable, target):
            yield item

    def __repr__(self) -> str:
        state = (
            "pending"
            if self._callable_result is _MISSING_VALUE
            else repr(self._callable_result)
        )
        return f"<LazyAwait {state}>"
