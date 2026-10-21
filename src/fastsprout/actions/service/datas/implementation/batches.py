"""Execute CRUD dependencies and backend writes on bounded input chunks."""

from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import aclosing
from functools import wraps
from operator import add
from typing import Annotated, Concatenate, Protocol

from annotated_types import Ge

from fastsprout.core.depends.invocation import (
    DependencyOwnable,
    with_dependencies,
)
from fastsprout.core.depends.scope import async_invocation_scope
from fastsprout.core.types import AnyIterable, Chunk, LazyAwait
from fastsprout.data.entity import Entitieable
from fastsprout.data.streams.implementation.base_common_stream import (
    BaseCommonStream,
)
from fastsprout.data.types import Valuable
from fastsprout.data.utils.iterable import chunked, resolve_any_iterable

__all__ = ["batch_count", "batch_stream"]


class BatchOwnable(DependencyOwnable, Protocol):
    chunk_size: Annotated[int, Ge(1)]


class Batch[T]:
    """Allow dependencies to inspect a bounded batch before it is written."""

    def __init__(self, values: Sequence[T]) -> None:
        self.values = values

    def __aiter__(self) -> AsyncIterator[T]:
        return resolve_any_iterable(self.values)


def batches[Owner: BatchOwnable, Input, Result, **P](
    function: Callable[
        Concatenate[Owner, AnyIterable[Input], P], Awaitable[Result]
    ],
) -> Callable[Concatenate[Owner, AnyIterable[Input], P], AsyncIterator[Result]]:
    run = with_dependencies(function)

    @wraps(function)
    def call(
        owner: Owner,
        values: AnyIterable[Input],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> AsyncIterator[Result]:
        size = owner.chunk_size
        if size <= 0:
            raise ValueError("chunk_size must be positive")

        async def iterate() -> AsyncIterator[Result]:
            async with (
                async_invocation_scope(),
                aclosing(resolve_any_iterable(chunked(values, size))) as chunks,
            ):
                async for chunk in chunks:
                    yield await run(
                        owner,
                        Chunk(Batch(chunk)),
                        *args,
                        **kwargs,
                    )

        return iterate()

    return call


def batch_stream[
    Owner: BatchOwnable,
    Input,
    Result: Valuable | Entitieable,
    **P,
](
    function: Callable[
        Concatenate[Owner, AnyIterable[Input], P], Awaitable[Sequence[Result]]
    ],
) -> Callable[
    Concatenate[Owner, AnyIterable[Input], P], BaseCommonStream[Result]
]:
    run = batches(function)

    @wraps(function)
    def call(
        owner: Owner,
        values: AnyIterable[Input],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> BaseCommonStream[Result]:
        chunks = run(owner, values, *args, **kwargs)

        async def iterate() -> AsyncIterator[Result]:
            async with aclosing(resolve_any_iterable(chunks)) as source:
                async for results in source:
                    for result in results:
                        yield result

        return BaseCommonStream(iterate())

    return call


def batch_count[Owner: BatchOwnable, Input, **P](
    function: Callable[
        Concatenate[Owner, AnyIterable[Input], P], Awaitable[int]
    ],
) -> Callable[Concatenate[Owner, AnyIterable[Input], P], LazyAwait[int]]:
    run = batches(function)

    @wraps(function)
    def call(
        owner: Owner,
        values: AnyIterable[Input],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> LazyAwait[int]:
        return BaseCommonStream(run(owner, values, *args, **kwargs)).reduce(
            add, 0
        )

    return call
