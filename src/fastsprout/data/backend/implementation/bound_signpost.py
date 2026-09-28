from collections.abc import Callable

from fastsprout.data.streams.context import StreamContext

from .signpost import Signpost


class BoundSignpost[T](Signpost[T]):
    """A private signpost for one DataR context; the entity's stays unchanged."""

    def __init__(
        self, factory: Callable[[], T], context: StreamContext, *, priority: int
    ) -> None:
        super().__init__(factory, priority=priority)
        self.context = context
