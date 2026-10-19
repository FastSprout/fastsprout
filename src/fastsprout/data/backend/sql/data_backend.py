import asyncio
from abc import ABC
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import (
    AbstractAsyncContextManager,
    aclosing,
    asynccontextmanager,
)
from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from fastsprout.core import Undefined, UndefinedType
from fastsprout.data.backend.implementation.data_backend import BaseDataBackend
from fastsprout.data.backend.sql.finalizer import SQLFinalizable
from fastsprout.data.capabilities.query import And, BaseQuery, Expression
from fastsprout.data.capabilities.query.predicate import evaluate
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import Entitieable, Signpostable
from fastsprout.data.streams.implementation import (
    JoinedStream,
    SimpleAsyncValueStream,
)
from fastsprout.events import EventBus
from fastsprout.events.event import Eventable

__all__ = ["SQLDataBackend", "prepare_query"]


def prepare_query[E: Entitieable, StatementT, R](
    query: BaseQuery[E, StatementT, R], native: bool
) -> tuple[StatementT, BaseQuery[E, StatementT, R] | None]:
    fallback = None if native else query.copy()
    if fallback is not None:
        query = query.unpaged()
        query.conditions = ()
    return query.build(), fallback


def row_predicate[E: Entitieable, R, *Ts](
    query: BaseQuery[E, Select[tuple[E, *Ts]], R],
) -> Callable[[tuple[E, *Ts]], Awaitable[bool]]:
    condition: Expression[E] = And(*query.conditions)

    async def matching(row: tuple[E, *Ts]) -> bool:
        return await evaluate(condition, row[0])

    return matching


class SQLDataBackend(
    BaseDataBackend[AbstractAsyncContextManager[AsyncSession], SQLFinalizable],
    ABC,
):
    def __init__(
        self,
        /,
        signpost: Signpostable[AbstractAsyncContextManager[AsyncSession]],
        *,
        bus: EventBus | UndefinedType | None = Undefined,
    ) -> None:
        super().__init__(signpost, bus=bus)
        self.__waited_events: list[Eventable] = []

    @asynccontextmanager
    async def bind(self):
        """Yield the shared finalizer for this SQL session."""
        async with self._signpost.factory() as session:
            flow = session.info.get("fastsprout_finalizer")
            if not isinstance(flow, SQLFinalizable):
                flow = session.info["fastsprout_finalizer"] = SQLFinalizable(
                    session
                )
            yield flow

    @asynccontextmanager
    async def session(self):
        async with self.bind() as flow:
            async with flow.session() as session:
                yield session

    async def scalars[T](
        self, statement: Select[tuple[T]]
    ) -> AsyncGenerator[T, None]:
        async with self.session() as session:
            result = await session.stream(
                statement,
                execution_options={"yield_per": DEFAULT_ITERATION_CHUNK_SIZE},
            )
            try:
                async for item in result.scalars():
                    self._check_stream_context()
                    yield item
            finally:
                await result.close()

    async def rows[*Ts](
        self, statement: Select[tuple[*Ts]]
    ) -> AsyncGenerator[tuple[*Ts], None]:
        async with self.session() as session:
            result = await session.stream(
                statement,
                execution_options={"yield_per": DEFAULT_ITERATION_CHUNK_SIZE},
            )
            try:
                async for row in result.tuples():
                    self._check_stream_context()
                    yield row
            finally:
                await result.close()

    def stream_rows[E: Entitieable, R, *Ts](
        self,
        query: BaseQuery[E, Select[tuple[E, *Ts]], R],
        *,
        native_conditions: bool,
    ) -> JoinedStream[E, *Ts]:
        statement, fallback = prepare_query(query, native_conditions)
        if fallback is None:
            return JoinedStream.from_factory(partial(self.rows, statement))

        async def rows() -> AsyncGenerator[tuple[E, *Ts], None]:
            async with aclosing(self.rows(statement)) as source:
                stream = (
                    SimpleAsyncValueStream(source)
                    .filter(row_predicate(fallback))
                    .drop(fallback.offset_value)
                )
                if isinstance(fallback.limit_value, int):
                    stream = stream.take(fallback.limit_value)
                async for row in stream:
                    yield row

        return JoinedStream.from_factory(rows)

    @asynccontextmanager
    async def transaction(self):
        async with self.bind() as flow:
            try:
                async with flow.transaction() as transaction:
                    yield transaction
                if self.__waited_events:
                    flow.after_commit.append(
                        partial(super()._publish_to_bus, *self.__waited_events)
                    )
            finally:
                self.__waited_events.clear()

    async def _publish_to_bus[E: Eventable](self, /, *events: E) -> None:
        self.__waited_events.extend(events)
        await asyncio.sleep(0)
