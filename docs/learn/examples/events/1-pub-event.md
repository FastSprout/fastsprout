# 1. Pub Event

<!-- example-source: examples/events/01_pub_event.py -->

`@pub` publishes the event returned by an action. After calling `return_hero()`, the example asks the same bus for the returned event's `EventState`.

Run from the repository root:

```bash
uv run --extra events python examples/events/01_pub_event.py
```

## Source

```python
"""Publish an event returned by an action and look up its state."""

import asyncio

from fastsprout.events import Event, EventBus, EventState, pub

bus = EventBus()


class HeroEvent(Event):
    name: str
    power: str


@pub(bus=bus)
async def return_hero() -> HeroEvent:
    return HeroEvent(name="Spider-Man", power="spider")


async def main():
    e = await return_hero()

    event_state: EventState[HeroEvent] | None = await bus.get(e)

    print("Event State:", event_state)


asyncio.run(main())
```

## Result

`bus.get(e)` finds a state whose event is Spider-Man:

```text
Event State: EventState(event=HeroEvent(name='Spider-Man', power='spider'))
```
