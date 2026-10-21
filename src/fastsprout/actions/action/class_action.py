"""Typed actions and the direct-call execution wrapper."""

from collections.abc import Sequence

from fastsprout.core.action import Actionable
from fastsprout.core.depends import DependsClass
from fastsprout.core.depends.invocation import with_dependencies
from fastsprout.core.types.schema import Schema

__all__ = ["Action"]


class Action[I: Schema, O: Schema](Actionable[I, O]):
    """Base for a class action with one typed input and output."""

    dependencies: Sequence[DependsClass] = ()

    def __init__(
        self, *, dependencies: Sequence[DependsClass] | None = None
    ) -> None:
        if dependencies is not None:
            self.dependencies = dependencies

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        method = cls.__dict__.get("__call__")
        if method is not None:
            type.__setattr__(cls, "__call__", with_dependencies(method))
