"""Compose schema actions as one lazy async stream."""

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import aclosing
from typing import Generic, overload

from typing_extensions import TypeVar

from fastsprout.core.action import IteratorActionable
from fastsprout.core.types.schema import Schema

from .execution import execute, routed
from .fork import ForkResult
from .types import BranchHandler, WorkflowAction

__all__ = ["Workflow"]

InputT = TypeVar("InputT", bound=Schema)
OutputT = TypeVar("OutputT", bound=Schema)
SourceT = TypeVar("SourceT", bound=Schema | None, default=None)


class Workflow(
    IteratorActionable[InputT, OutputT], Generic[InputT, OutputT, SourceT]
):
    """Yield each step's results and pass each element to the next step."""

    @overload
    def __init__(
        self, first: Callable[[InputT], Awaitable[OutputT]]
    ) -> None: ...

    @overload
    def __init__(self, first: Callable[[InputT], OutputT]) -> None: ...

    @overload
    def __init__(self, first: WorkflowAction[InputT, OutputT]) -> None: ...

    def __init__(self, first: WorkflowAction[InputT, OutputT]) -> None:
        self.run = first
        self.branches: (
            tuple[
                Callable[[InputT], AsyncGenerator[SourceT, None]],
                Callable[[SourceT], BranchHandler[OutputT] | None],
            ]
            | None
        ) = None

    def __call__(self, payload: InputT) -> AsyncGenerator[OutputT, None]:
        return execute(self.run, payload).__aiter__()

    def then[N: Schema](
        self, next_action: WorkflowAction[OutputT, N]
    ) -> "Workflow[InputT, N]":
        next_workflow = Workflow(next_action)

        async def run(payload: InputT) -> AsyncGenerator[N, None]:
            async with aclosing(self(payload)) as source:
                async for value in source:
                    async with aclosing(next_workflow(value)) as results:
                        async for result in results:
                            yield result

        return Workflow(run)

    def fork[A: Schema, B: Schema](
        self,
        left: Callable[[OutputT], Awaitable[A]],
        right: Callable[[OutputT], Awaitable[B]],
    ) -> "Workflow[InputT, ForkResult[A, B]]":
        async def run(payload: OutputT) -> ForkResult[A, B]:
            left_result, right_result = await asyncio.gather(
                left(payload), right(payload)
            )
            return ForkResult(left=left_result, right=right_result)

        return self.then(run)

    def join[N: Schema](
        self, next_action: WorkflowAction[OutputT, N]
    ) -> "Workflow[InputT, N]":
        return self.then(next_action)

    @overload
    def branch[T: Schema, N: Schema](
        self: "Workflow[InputT, OutputT, None]",
        kind: type[T],
        handler: WorkflowAction[T, N],
    ) -> "Workflow[InputT, N, OutputT]": ...

    @overload
    def branch[T: Schema, N: Schema, Source: Schema | None](
        self: "Workflow[InputT, OutputT, Source]",
        kind: type[T],
        handler: WorkflowAction[T, N],
    ) -> "Workflow[InputT, OutputT | N, Source]": ...

    def branch[T: Schema, N: Schema, Source: Schema | None](
        self: "Workflow[InputT, OutputT, Source]",
        kind: type[T],
        handler: WorkflowAction[T, N],
    ) -> "Workflow[InputT, N, OutputT] | Workflow[InputT, OutputT | N, Source]":
        if self.branches is None:

            def first_match(value: OutputT) -> BranchHandler[N] | None:
                return (
                    (lambda: handler(value))
                    if isinstance(value, kind)
                    else None
                )

            return branch_workflow(self.__call__, first_match)

        source, previous_match = self.branches

        def match(value: Source) -> BranchHandler[OutputT | N] | None:
            previous = previous_match(value)
            if previous is not None:
                return previous
            return (lambda: handler(value)) if isinstance(value, kind) else None

        return branch_workflow(source, match)


def branch_workflow[Input: Schema, Output: Schema, Source: Schema | None](
    source: Callable[[Input], AsyncGenerator[Source, None]],
    match: Callable[[Source], BranchHandler[Output] | None],
) -> Workflow[Input, Output, Source]:
    workflow = Workflow[Input, Output, Source](routed(source, match))
    workflow.branches = source, match
    return workflow
