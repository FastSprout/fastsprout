import inspect
from collections.abc import (
    AsyncGenerator,
    Awaitable,
    Callable,
)
from contextlib import aclosing, nullcontext
from typing import overload

from typing_extensions import TypeIs

from .protocols.ables import ACloseable, AsyncIterableResolver

__all__ = ["LazyAwait"]


def is_awaitable[R](value: Awaitable[R] | R) -> TypeIs[Awaitable[R]]:
    return isinstance(value, Awaitable)


class LazyAwait[R](Awaitable[R]):
    __slots__ = ("factory", "result")

    @overload
    def __init__(self, factory: Callable[[], Awaitable[R]]) -> None: ...

    @overload
    def __init__(self, factory: Callable[[], R]) -> None: ...

    @overload
    def __init__(self, factory: Callable[[], Awaitable[R] | R]) -> None: ...

    def __init__(self, factory: Callable[[], Awaitable[R] | R]) -> None:
        self.factory = factory
        self.result: tuple[R] | None = None

    async def resolve(self) -> R:
        if self.result is None:
            pending = self.factory()
            self.result = (await pending if is_awaitable(pending) else pending,)
        return self.result[0]

    def __getattr__(self, name: str) -> Callable[..., "LazyAwait"]:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)

        def call(*args, **kwargs) -> LazyAwait:
            async def step():
                target = await self.resolve()
                result = getattr(target, name)(*args, **kwargs)
                if isinstance(result, LazyAwait) or inspect.isawaitable(result):
                    return await result
                return result

            return LazyAwait(step)

        return call

    def __await__(self):
        return self.resolve().__await__()

    async def __aiter__[T](
        self: AsyncIterableResolver[T],
    ) -> AsyncGenerator[T, None]:
        iterator = aiter(await self.resolve())
        scope = (
            aclosing(iterator)
            if isinstance(iterator, ACloseable)
            else nullcontext(iterator)
        )
        async with scope:
            async for item in iterator:
                yield item

    def __repr__(self) -> str:
        state = "pending" if self.result is None else repr(self.result[0])
        return f"<LazyAwait {state}>"
