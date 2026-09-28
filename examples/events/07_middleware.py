"""Run middleware for one event type and inspect its handler result."""

import asyncio
from typing import assert_type

from fastsprout.events import Event, EventBus, EventState, pub
from fastsprout.events.decorators import sub
from fastsprout.events.event import EventResult
from fastsprout.events.middleware import EventsMiddleware


class FirstEvent(Event): ...


class SecondEvent(Event): ...


class SimpleMiddlewareForFirstEvent:
    def __init__(self, bus: EventBus, /) -> None:
        self.bus = bus

    async def __call__(self, event_state: EventState[FirstEvent]) -> None:
        assert_type(event_state.event, FirstEvent)
        print("Event State:", event_state)
        result: EventResult[FirstEvent] = await event_state.wait()  # (1)!
        print("EventResult[FirstEvent]:", result)


bus = EventBus(
    middleware=[
        EventsMiddleware(SimpleMiddlewareForFirstEvent),  # (2)!
    ]
)


@pub(bus=bus)
async def return_events():
    return [FirstEvent(), SecondEvent()]


@sub(FirstEvent, bus=bus)
async def process_first_event(e: FirstEvent) -> None:
    return None


asyncio.run(return_events())
