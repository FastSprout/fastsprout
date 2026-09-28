# 4. Many Pub Events

<!-- example-source: examples/events/04_many_pub_events.py -->

A publisher may return several events. `@pub` publishes each returned `HeroEvent`; passing those events to `bus.get(*events)` retrieves their states as an `EventStatesGroup`.

Run from the repository root:

```bash
uv run --extra events python examples/events/04_many_pub_events.py
```

## Source

```python
"""Publish several events returned by one action."""

import asyncio
from collections.abc import Sequence

from fastsprout.events import Event, EventBus, pub
from fastsprout.events.event import EventStatesGroup

bus = EventBus()


class HeroEvent(Event):
    name: str
    power: str


@pub(bus=bus)
async def pub_event() -> list[HeroEvent]:
    return [
        HeroEvent(name="Spider-Man", power="spider"),
        HeroEvent(name="Batman", power="money"),
        HeroEvent(name="SuperMan", power="sun"),
    ]


async def main():
    e: Sequence[HeroEvent] = await pub_event()

    event_states: EventStatesGroup[*tuple[HeroEvent, ...]] = await bus.get(*e)

    print("Event States:", event_states)


asyncio.run(main())
```

## Result

The group contains three states for Spider-Man, Batman, and SuperMan:

```text
Event States: EventStatesGroup(EventState(event=HeroEvent(name='Spider-Man', power='spider')), EventState(event=HeroEvent(name='Batman', power='money')), EventState(event=HeroEvent(name='SuperMan', power='sun')))
```
