from abc import ABC

from fastsprout.core import Undefined, UndefinedType
from fastsprout.data.entity import Signpostable
from fastsprout.events import EventBus
from fastsprout.events.bus import IN_MEMORY_EVENT_BUS
from fastsprout.events.event import Eventable

from ..protocols import Backendable, Finalizable
from .bound_signpost import BoundSignpost

__all__ = ["BaseDataBackend"]


class BaseDataBackend[T, F: Finalizable](Backendable[T, F], ABC):
    """Base class for data backends.

    Class hierarchy may be abstract (framework machinery like SQLDataBackend
    and capability mixins), but only concrete classes — all type
    parameters bound, no abstract methods left — can be instantiated.
    """

    def __init__(
        self,
        /,
        signpost: Signpostable[T],
        *,
        bus: EventBus | UndefinedType | None = Undefined,
    ) -> None:
        self.signpost = signpost
        self.bus: EventBus | None = (
            IN_MEMORY_EVENT_BUS if isinstance(bus, UndefinedType) else bus
        )

    @property
    def with_events(self) -> bool:
        return bool(self.bus)

    def check_stream_context(self) -> None:
        if isinstance(self.signpost, BoundSignpost):
            self.signpost.context.check()

    async def publish_to_bus(self, /, *events: Eventable) -> None:
        if self.bus is not None:
            await self.bus.publish(*events)
