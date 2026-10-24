"""Apply router dependencies before backend operations and lazy reads."""

import inspect
from asyncio import current_task
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
    Sequence,
)
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Protocol

from fastsprout.core.depends import DependsClass, inject_depends
from fastsprout.data.backend.implementation.bound_signpost import BoundSignpost
from fastsprout.data.backend.protocols import DataAbilitable, Finalizable
from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.entity import Entitieable, Signpostable
from fastsprout.data.router.protocols import Routerable
from fastsprout.data.streams.protocols import AsyncEntityStreamable
from fastsprout.events import EventBus

__all__ = ["AbilityDependencies", "AsyncOperationable", "guard_ability"]


class AsyncOperationable[**P, R](Protocol):
    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...


class AbilityDependencies:
    def __init__(
        self, datar: Routerable, dependencies: Sequence[DependsClass]
    ) -> None:
        self.datar = datar
        self.dependencies = dependencies
        self.active: ContextVar[int | None] = ContextVar(
            "fastsprout_ability_active", default=None
        )

    async def check[**P, R](
        self, function: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        if self.active.get() == id(current_task()):
            return
        supplied = inspect.signature(function).bind(*args, **kwargs)
        supplied.apply_defaults()
        supplied.arguments.update(operation=function.__name__, datar=self.datar)
        await inject_depends.ainject(
            function,
            args,
            kwargs,
            extra_dependencies=self.dependencies,
            supplied=supplied,
        )

    def coroutine[**P, R](
        self,
        function: Callable[P, Awaitable[R]],
    ) -> AsyncOperationable[P, R]:
        @wraps(function)
        async def call(*args: P.args, **kwargs: P.kwargs) -> R:
            await self.check(function, *args, **kwargs)
            token = self.active.set(id(current_task()))
            try:
                return await function(*args, **kwargs)
            finally:
                self.active.reset(token)

        return call

    def iterator[**P, R](
        self,
        function: Callable[P, AsyncIterator[R]],
    ) -> Callable[P, AsyncIterator[R]]:
        @wraps(function)
        async def iterate(
            *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[R]:
            await self.check(function, *args, **kwargs)
            stream = function(*args, **kwargs)
            try:
                while True:
                    token = self.active.set(id(current_task()))
                    try:
                        item = await anext(stream)
                    except StopAsyncIteration:
                        return
                    finally:
                        self.active.reset(token)
                    yield item
            finally:
                if isinstance(stream, AsyncGenerator):
                    await stream.aclose()

        return iterate

    def stream[ProductT, **P](
        self,
        signpost: Signpostable[AbstractAsyncContextManager[ProductT]],
        read: Callable[P, Awaitable[None]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> BoundSignpost[AbstractAsyncContextManager[ProductT]]:
        @asynccontextmanager
        async def factory() -> AsyncIterator[ProductT]:
            await self.check(read, *args, **kwargs)
            async with signpost.factory() as product:
                yield product

        if not isinstance(signpost, BoundSignpost):
            raise TypeError("A router stream requires its bound signpost")
        return BoundSignpost(
            factory, signpost.context, priority=signpost.priority
        )


def guard_ability[
    E: Entitieable,
    StatementT,
    ProductT,
    F: Finalizable,
](
    ability: DataAbilitable[
        E, AbstractAsyncContextManager[ProductT], BaseQuery[E, StatementT], F
    ],
    signpost: Signpostable[AbstractAsyncContextManager[ProductT]],
    datar: Routerable,
    dependencies: Sequence[DependsClass],
    bus: EventBus | None,
) -> None:
    guard = AbilityDependencies(datar, dependencies)

    def stream(query: BaseQuery[E, StatementT], /) -> AsyncEntityStreamable[E]:
        async def read(query: BaseQuery[E, StatementT]) -> None:
            """Provide the read operation's arguments to dependencies."""

        checked = guard.stream(signpost, read, query)
        return type(ability)(checked, bus=bus).stream(query)

    ability.create = guard.coroutine(ability.create)
    ability.bulk_create = guard.coroutine(ability.bulk_create)
    ability.update = guard.coroutine(ability.update)
    ability.bulk_update = guard.coroutine(ability.bulk_update)
    ability.upsert = guard.coroutine(ability.upsert)
    ability.bulk_upsert = guard.coroutine(ability.bulk_upsert)
    ability.delete = guard.coroutine(ability.delete)
    ability.bulk_delete = guard.coroutine(ability.bulk_delete)
    ability.delete_by_query = guard.coroutine(ability.delete_by_query)
    ability.update_by_query = guard.coroutine(ability.update_by_query)
    ability.find_first = guard.coroutine(ability.find_first)
    ability.find_exactly_one = guard.coroutine(ability.find_exactly_one)
    ability.find_all = guard.coroutine(ability.find_all)
    ability.iter_bulk_create = guard.iterator(ability.iter_bulk_create)
    ability.iter_bulk_update = guard.iterator(ability.iter_bulk_update)
    ability.iter_bulk_upsert = guard.iterator(ability.iter_bulk_upsert)
    ability.iter = guard.iterator(ability.iter)
    ability.iter_per = guard.iterator(ability.iter_per)
    ability.stream = stream
