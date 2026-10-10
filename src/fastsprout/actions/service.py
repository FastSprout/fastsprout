"""Group typed actions and resolve their dependencies."""

from collections.abc import Sequence
from typing import ClassVar

from fastsprout.core.action import BaseActionGroup
from fastsprout.core.depends import DependsClass

from .action.decorator_action import decorate_action_group

__all__ = ["Service", "decorate_action_group"]


class Service(BaseActionGroup):
    __action_group__: ClassVar[bool] = True
    dependencies: Sequence[DependsClass] = ()

    def __init__(
        self, *, dependencies: Sequence[DependsClass] | None = None
    ) -> None:
        if dependencies is not None:
            self.dependencies = dependencies

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        decorate_action_group(cls)
