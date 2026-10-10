from collections.abc import Awaitable, Callable

from fastsprout.core.types import AnyIterable
from fastsprout.core.types.schema import Schema

__all__ = ["BranchHandler", "WorkflowAction", "WorkflowResult"]

type WorkflowResult[O: Schema] = O | AnyIterable[O] | None
type WorkflowAction[I: Schema, O: Schema] = Callable[
    [I], Awaitable[WorkflowResult[O]] | WorkflowResult[O]
]
type BranchHandler[O: Schema] = Callable[
    [], Awaitable[WorkflowResult[O]] | WorkflowResult[O]
]
