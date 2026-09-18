from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from types import TracebackType
from typing import Any, Self

from fastsprout.data.backend.implementation.bound_signpost import BoundSignpost
from fastsprout.data.backend.protocols import (
    Backendable,
    DataAbilitable,
    Finalizable,
)
from fastsprout.data.backend.sql import SQLEntity
from fastsprout.data.backend.sql.capabilities import SQLAbilitable
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.entity import Entitieable, Signpostable
from fastsprout.data.router.exceptions import DataRError, NoBackendError
from fastsprout.data.router.protocols import Routerable
from fastsprout.data.streams.context import StreamContext
from fastsprout.data.streams.implementation import JoinedStream
from fastsprout.data.streams.protocols import AsyncEntityStream

from .routed_join import RoutedJoin

__all__ = ["DataR"]


def backend_of[E: Entitieable[Any]](
    entity: type[E],
) -> type[Backendable[Any, Finalizable]]:
    match entity:
        case entity if issubclass(entity, SQLEntity):
            return SQLDataBackend
        case _:
            raise NoBackendError(f"Not found backend for entity: {entity}")


def ability_of[E: Entitieable[Any]](
    entity: type[E],
) -> type[DataAbilitable[E, Any, BaseQuery[E, Any], Finalizable]]:
    match entity:
        case entity if issubclass(entity, SQLEntity):
            return SQLAbilitable
        case _:
            raise NoBackendError(f"Not found backend for entity: {entity}")


class Bindinger(Finalizable):
    """Per-context signpost registry.

    Every signpost touched in a DataR context is registered once, its
    private factory wrapped so that all binds in the context share ONE opened
    product (e.g. one AsyncSession per signpost). Finalize/abort walk
    registered signposts in priority order and settle the shared
    products through their backends.
    """

    def __init__(self) -> None:
        self.__signposts: dict[int, Signpostable[Any]] = {}
        self.__entities: dict[int, type[Entitieable[Any]]] = {}
        self.__opened: dict[int, tuple[Any, Any]] = {}
        self.__context = StreamContext()

    def add[E: Entitieable[Any]](self, entity: type[E]) -> Signpostable[Any]:
        signpost = entity.__signpost__
        signpost_id = id(signpost)
        if signpost_id not in self.__signposts:
            bound = BoundSignpost(
                self.__shared_factory(signpost_id, signpost.factory),
                self.__context,
                priority=signpost.priority,
            )
            self.__signposts[signpost_id] = bound
            self.__entities[id(bound)] = entity
        return self.__signposts[signpost_id]

    def __shared_factory(
        self, signpost_id: int, original: Callable[[], Any]
    ) -> Callable[[], AbstractAsyncContextManager[Any]]:
        @asynccontextmanager
        async def shared() -> AsyncIterator[Any]:
            self.__context.check()
            if signpost_id not in self.__opened:
                manager = original()
                product = await manager.__aenter__()
                self.__opened[signpost_id] = (manager, product)
            yield self.__opened[signpost_id][1]

        return shared

    async def close(self) -> None:
        """Invalidate streams and release this context's opened products."""
        self.__context.close()
        for manager, _ in self.__opened.values():
            await manager.__aexit__(None, None, None)
        self.__opened.clear()

    def __ordered(self) -> list[Signpostable[Any]]:
        return sorted(
            self.__signposts.values(),
            key=lambda signpost: signpost.priority,
            reverse=True,
        )

    def __backend_flow(
        self, signpost: Signpostable[Any]
    ) -> AbstractAsyncContextManager[Finalizable]:
        entity = self.__entities[id(signpost)]
        return backend_of(entity)(signpost).bind()

    async def finalize(self) -> None:
        """Settle bound backends — highest `priority` first."""
        for signpost in self.__ordered():
            async with self.__backend_flow(signpost) as flow:
                await flow.finalize()

    async def abort(self) -> None:
        """Abort bound backends — lowest `priority` first."""
        for signpost in reversed(self.__ordered()):
            async with self.__backend_flow(signpost) as flow:
                await flow.abort()


class DataR(Routerable):
    def __init__(self) -> None:
        self.__bindings: Bindinger | None = None

    async def __aenter__(self) -> Self:
        self.__bindings = Bindinger()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        bindings, self.__bindings = self.__bindings, None
        if bindings is None:
            return
        try:
            if exc_type is None:
                await bindings.finalize()
            else:
                await bindings.abort()
        finally:
            await bindings.close()

    @property
    def __init_bindings__(self) -> Bindinger:
        if self.__bindings is None:
            raise DataRError("DataR is not initialized!")
        return self.__bindings

    def ability[E: Entitieable[Any]](
        self, entity: type[E]
    ) -> DataAbilitable[E, Any, BaseQuery[E, Any], Finalizable]:
        signpost = self.__init_bindings__.add(entity)
        return ability_of(entity)(signpost)

    def stream[E: Entitieable[Any]](
        self, q: BaseQuery[E, Any]
    ) -> AsyncEntityStream[E]:
        if isinstance(q, BaseQuery):
            self.__init_bindings__.add(q.entity)
            ability = self.ability(q.entity)
            return ability.stream(q)
        raise DataRError(f"Not supported source: {q}")

    def join[E: Entitieable[Any], StatementT](
        self, q: BaseQuery[E, StatementT]
    ) -> RoutedJoin[E]:
        """Start a lazy inner join; consume it inside this DataR context."""
        return RoutedJoin(self, JoinedStream(self.stream(q)))

    async def finalize(self) -> None:
        """Flush staged intents, then finalize bound backends —
        highest `priority` first."""
        await self.__init_bindings__.finalize()

    async def abort(self) -> None:
        """Drop staged intents and abort bound backends."""
        await self.__init_bindings__.abort()
