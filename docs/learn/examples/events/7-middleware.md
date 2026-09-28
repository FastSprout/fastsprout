# 7. Middleware

<!-- example-source: examples/events/07_middleware.py -->

`EventsMiddleware` runs `SimpleMiddlewareForFirstEvent` only for `FirstEvent`. The middleware receives the typed `EventState` and can await its handler result. `SecondEvent` is published by the same action but does not use this middleware.

Run from the repository root:

```bash
uv run --extra events python examples/events/07_middleware.py
```

## Source

```python
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
```

1. `wait()` returns the results collected for this particular event state.
2. The wrapper inspects the middleware's typed `EventState` parameter to select events.

## Result

The middleware prints the event state and its result. The result has no returned
values or pending handlers because the subscriber returns `None`.

```text
Event State: EventState(event=FirstEvent())
EventResult[FirstEvent]: EventResult(state=EventState(event=FirstEvent()), values=[], pending=0, errors=[])
```
