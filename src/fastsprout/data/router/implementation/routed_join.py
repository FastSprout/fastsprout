from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.implementation import JoinedStream
from fastsprout.data.streams.implementation.joined_stream import JoinKey

if TYPE_CHECKING:
    from fastsprout.data.router.protocols import Routerable


class RoutedJoin[*Ts]:
    """Internal adapter routing join queries through the same DataR context."""

    def __init__(self, router: "Routerable", joined: JoinedStream[*Ts]) -> None:
        self._router = router
        self._joined = joined

    def join[E: Entitieable[Any], StatementT](
        self,
        q: BaseQuery[E, StatementT],
        *,
        on: tuple[JoinKey[tuple[*Ts]], JoinKey[E]],
    ) -> "RoutedJoin[*Ts, E]":
        return RoutedJoin(
            self._router,
            self._joined.join(self._router.stream(q), on=on),
        )

    def __aiter__(self) -> AsyncGenerator[tuple[*Ts], None]:
        return self._joined.__aiter__()

    async def to_list(self) -> list[tuple[*Ts]]:
        return await self._joined.to_list()
