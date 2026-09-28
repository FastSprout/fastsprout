# 6. Pub Schedule Event

<!-- example-source: examples/events/06_pub_schedule_event.py -->

`@pub(on="* * * * * *")` schedules a publisher for every second while `bus.scheduler()` is active. The example keeps the scheduler open long enough for one tick and waits for the resulting event.

Run from the repository root:

```bash
uv run --extra events python examples/events/06_pub_schedule_event.py
```

## Source

```python
"""Run a cron-scheduled publisher while the bus scheduler is active."""

import asyncio
from collections.abc import AsyncIterator

from fastsprout.events import EventBus, ScheduleEvent, pub, sub
from fastsprout.events.event import EventState

bus = EventBus()
triggered = asyncio.Event()


class HeroEvent(ScheduleEvent):
    name: str
    power: str


@pub(bus=bus, on="* * * * * *")
async def pub_hero_event() -> HeroEvent:
    return HeroEvent(name="Spider-Man", power="spider")


@sub(HeroEvent, bus=bus)
async def sub_hero_event(e: HeroEvent) -> None:
    print("HeroEvent:", e)
    triggered.set()
    return None


async def main() -> None:
    async with bus.scheduler():
        await triggered.wait()
        event_state: AsyncIterator[EventState[HeroEvent]] = await bus.get(
            HeroEvent
        )
        result = await (await anext(event_state)).wait()
        print("Event Result:", result.state.event.name)


asyncio.run(main())
```

## Result

The subscriber prints a Spider-Man event, followed by its result:

```text
HeroEvent: name='Spider-Man' power='spider'
Event Result: Spider-Man
```
