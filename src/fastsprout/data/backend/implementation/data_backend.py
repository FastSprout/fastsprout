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
        cls = type(self)
        if getattr(cls, "__abstractmethods__", None):
            raise TypeError(f"{cls.__name__} is an abstract backend")
        self._signpost = signpost
        self.__bus = (
            IN_MEMORY_EVENT_BUS if isinstance(bus, UndefinedType) else bus
        )

    @property
    def with_events(self) -> bool:
        return bool(self.__bus)

    def _check_stream_context(self) -> None:
        if isinstance(self._signpost, BoundSignpost):
            self._signpost.context.check()

    async def _publish_to_bus[E: Eventable](self, /, *events: E) -> None:
        if self.__bus is not None:
            await self.__bus.publish(*events)
