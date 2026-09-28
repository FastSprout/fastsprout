from collections.abc import Callable
from typing import Annotated

from annotated_types import Ge

from fastsprout.data.entity import Signpostable

__all__ = ["Signpost"]


class Signpost[T](Signpostable[T]):
    """Concrete signpost: holds the factory and the priority."""

    def __init__(
        self, factory: Callable[[], T], *, priority: Annotated[int, Ge(0)] = 0
    ) -> None:
        self._factory = factory
        self.priority = priority

    def factory(self) -> T:
        return self._factory()
