# 1. Pub Pusher

<!-- example-source: examples/events/01_decorators_01_pub_pusher.py -->

Publish an event returned by an action and look up its state.

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

```text
Event State: EventState(event=HeroEvent(name='Spider-Man', power='spider'))
```
