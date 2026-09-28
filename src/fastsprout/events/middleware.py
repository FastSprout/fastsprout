from __future__ import annotations

import inspect
from typing import (
    TYPE_CHECKING,
    Protocol,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from fastsprout.events.event import Eventable, EventState

if TYPE_CHECKING:
    from fastsprout.events.bus import EventBus

__all__ = ["EventsMiddleware", "EventsMiddlewareFactory"]


class EventsMiddlewareFactory[**P](Protocol):
    def __init__(
        self, bus: EventBus, /, *args: P.args, **kwargs: P.kwargs
    ) -> None: ...

    async def __call__(self, *args, **kwargs) -> None: ...


class EventsMiddleware[**P]:
    def __init__(
        self,
        cls: type[EventsMiddlewareFactory[P]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        self.cls = cls
        self.args = args
        self.kwargs = kwargs

    def accepts(self, event: Eventable) -> bool:
        parameters = list(inspect.signature(self.cls.__call__).parameters)
        if len(parameters) < 2:
            return True
        annotation = get_type_hints(self.cls.__call__).get(parameters[1])
        if get_origin(annotation) is not EventState:
            return True
        event_type = get_args(annotation)[0]
        return not isinstance(event_type, type) or isinstance(
            event, event_type
        )

    def bind(self, bus: EventBus) -> EventsMiddlewareFactory[P]:
        return cast(
            EventsMiddlewareFactory[P],
            self.cls(bus, *self.args, **self.kwargs),
        )

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        args_strings = [f"{value!r}" for value in self.args]
        option_strings = [
            f"{key}={value!r}" for key, value in self.kwargs.items()
        ]
        name = getattr(self.cls, "__name__", "")
        args_repr = ", ".join([name, *args_strings, *option_strings])
        return f"{class_name}({args_repr})"
