from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import (
    TYPE_CHECKING,
    Protocol,
    TypeGuard,
    get_args,
    get_origin,
    get_type_hints,
)

from fastsprout.events.event import Eventable, EventState

if TYPE_CHECKING:
    from fastsprout.events.bus import EventBus

__all__ = [
    "EventsMiddleware",
    "EventsMiddlewareFactoryable",
    "MiddlewareBindable",
]


class EventsMiddlewareFactoryable[E: Eventable, **P](Protocol):
    def __init__(
        self, bus: EventBus, /, *args: P.args, **kwargs: P.kwargs
    ) -> None: ...

    async def __call__(self, state: EventState[E], /) -> None: ...


class MiddlewareBindable(Protocol):
    def resolve(
        self, bus: EventBus
    ) -> Callable[[EventState[Eventable]], Awaitable[None]]: ...


class EventsMiddleware[E: Eventable, **P]:
    def __init__(
        self,
        cls: type[EventsMiddlewareFactoryable[E, P]],
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
        return not isinstance(event_type, type) or isinstance(event, event_type)

    def accepts_state(
        self, state: EventState[Eventable]
    ) -> TypeGuard[EventState[E]]:
        return self.accepts(state.event)

    def bind(self, bus: EventBus) -> EventsMiddlewareFactoryable[E, P]:
        return self.cls(bus, *self.args, **self.kwargs)

    def resolve(
        self, bus: EventBus
    ) -> Callable[[EventState[Eventable]], Awaitable[None]]:
        handler = self.bind(bus)

        async def call(state: EventState[Eventable]) -> None:
            if self.accepts_state(state):
                await handler(state)

        return call

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        args_strings = [f"{value!r}" for value in self.args]
        option_strings = [
            f"{key}={value!r}" for key, value in self.kwargs.items()
        ]
        name = getattr(self.cls, "__name__", "")
        args_repr = ", ".join([name, *args_strings, *option_strings])
        return f"{class_name}({args_repr})"
