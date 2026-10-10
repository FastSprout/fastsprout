from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import aclosing, nullcontext

from fastsprout.core.decorators.lazy_await import lazy_await
from fastsprout.core.depends.scope import invocation_scope
from fastsprout.core.types.schema import Schema
from fastsprout.data.utils.iterable import resolve_any_iterable

from .types import BranchHandler, WorkflowAction, WorkflowResult

__all__ = ["execute", "resolve_result", "routed"]


async def resolve_result[O: Schema](
    result: WorkflowResult[O] | Awaitable[WorkflowResult[O]],
) -> AsyncGenerator[O, None]:
    if isinstance(result, Awaitable):
        result = await result
    if isinstance(result, Schema):
        yield result
    elif result is not None:
        iterator = resolve_any_iterable(result)
        scope = (
            aclosing(iterator)
            if isinstance(iterator, AsyncGenerator)
            else nullcontext(iterator)
        )
        async with scope:
            async for item in iterator:
                yield item


@lazy_await
async def execute[I: Schema, O: Schema](
    action: WorkflowAction[I, O], payload: I
) -> AsyncGenerator[O, None]:
    if not isinstance(payload, Schema):
        raise TypeError("Workflow input must be a Schema")
    with invocation_scope():
        async with aclosing(resolve_result(action(payload))) as results:
            async for result in results:
                yield result


def routed[Input: Schema, Output: Schema, Source: Schema | None](
    source: Callable[[Input], AsyncGenerator[Source, None]],
    match: Callable[[Source], BranchHandler[Output] | None],
) -> Callable[[Input], AsyncGenerator[Output, None]]:
    async def run(payload: Input) -> AsyncGenerator[Output, None]:
        async with aclosing(source(payload)) as values:
            async for value in values:
                handler = match(value)
                if handler is None:
                    raise LookupError(
                        f"No workflow branch for {type(value).__name__}"
                    )
                async with aclosing(resolve_result(handler())) as results:
                    async for result in results:
                        yield result

    return run
