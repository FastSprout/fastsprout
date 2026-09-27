from collections.abc import Sequence
from datetime import timedelta
from functools import wraps
from typing import Any, Protocol, cast, overload

from fastsprout.core import Depends
from fastsprout.core.action import (
    BaseAction,
    BaseNullableAction,
    BaseSequenceAction,
    BaseSequenceTriggerAction,
    BaseTriggerAction,
)
from fastsprout.core.depends import DependsClass, inject_depends
from fastsprout.core.schema import BaseSchema
from fastsprout.events.bus import EventBus
from fastsprout.events.event import Event, ScheduleEvent

__all__ = ["pub", "sub"]


class PubDecorator(Protocol):
    @overload
    def __call__[E: Event, R: BaseSchema](
        self,
        func: BaseAction[E, R],
    ) -> BaseAction[E, R]: ...

    @overload
    def __call__[E: Event, R: BaseSchema | None](
        self,
        func: BaseNullableAction[E, R],
    ) -> BaseNullableAction[E, R]: ...

    @overload
    def __call__[T: Event](
        self,
        func: BaseTriggerAction[T],
    ) -> BaseTriggerAction[T]: ...

    @overload
    def __call__[T: Event](
        self,
        func: BaseSequenceTriggerAction[T],
    ) -> BaseSequenceTriggerAction[T]: ...


class SchedulePubDecorator(Protocol):
    @overload
    def __call__[T: ScheduleEvent](
        self,
        func: BaseTriggerAction[T],
    ) -> BaseTriggerAction[T]: ...

    @overload
    def __call__[T: ScheduleEvent](
        self,
        func: BaseSequenceTriggerAction[T],
    ) -> BaseSequenceTriggerAction[T]: ...


class SubDecorator(Protocol):
    @overload
    def __call__[E: Event, R: BaseSchema | None](
        self,
        func: BaseNullableAction[E, R],
    ) -> BaseNullableAction[E, R]: ...

    @overload
    def __call__[E: Event, R: BaseSchema](
        self,
        func: BaseSequenceAction[E, R],
    ) -> BaseSequenceAction[E, R]: ...

    @overload
    def __call__[E: Event, R: BaseSchema](
        self,
        func: BaseAction[E, R],
    ) -> BaseAction[E, R]: ...


async def _publish_result(bus: EventBus, result: Any) -> None:
    if isinstance(result, Event):
        await bus.publish(result)
    elif isinstance(result, Sequence):
        events = tuple(item for item in result if isinstance(item, Event))
        if events:
            await bus.publish(*events)


@overload
def pub(
    *,
    bus: EventBus = Depends(),  # noqa: B008
    on: str | timedelta,
) -> SchedulePubDecorator: ...


@overload
def pub(*, bus: EventBus = Depends(), on: None = None) -> PubDecorator: ...  # noqa: B008


def pub(
    *,
    bus: EventBus = Depends(),  # noqa: B008
    on: str | timedelta | None = None,
) -> PubDecorator | SchedulePubDecorator:
    def wrapper(func: Any) -> Any:
        injected_func = inject_depends(func)

        @wraps(func)
        async def publish_result(*args: Any, **kwargs: Any) -> Any:
            selected_bus = (
                await inject_depends.aresolve(bus, EventBus)
                if isinstance(bus, DependsClass)
                else bus
            )
            result = await injected_func(*args, **kwargs)
            await _publish_result(selected_bus, result)
            return result

        if on is not None:
            selected_bus = (
                inject_depends.resolve(bus, EventBus)
                if isinstance(bus, DependsClass)
                else bus
            )
            selected_bus.schedule(on, publish_result)

        return publish_result

    return cast(PubDecorator, wrapper)


def sub[T: Event, R: BaseSchema](
    *event_types: type[T],
    bus: EventBus = Depends(),  # noqa: B008
) -> SubDecorator:
    def wrapper(func: Any) -> Any:
        injected_func = inject_depends(func)
        selected_bus = (
            inject_depends.resolve(bus, EventBus)
            if isinstance(bus, DependsClass)
            else bus
        )
        for event_type in event_types:
            selected_bus.subscribe(event_type, injected_func)
        return injected_func

    return cast(SubDecorator, wrapper)
