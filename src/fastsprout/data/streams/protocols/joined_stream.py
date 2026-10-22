from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    Callable,
    Hashable,
)
from typing import Protocol

__all__ = ["AsyncJoinedStreamable", "JoinKey"]

type JoinKey[T] = Callable[[T], Hashable | Awaitable[Hashable]]


class AsyncJoinedStreamable[*Ts](Protocol):
    def join[T](
        self,
        stream: AsyncIterable[T],
        *,
        on: tuple[JoinKey[tuple[*Ts]], JoinKey[T]],
    ) -> "AsyncJoinedStreamable[*Ts, T]": ...

    def __aiter__(self) -> AsyncGenerator[tuple[*Ts], None]: ...

    async def to_list(self) -> list[tuple[*Ts]]: ...
