# 3. Event Group In Bus

<!-- example-source: examples/events/02_advance_decorators/01_events_group/03_event_group_in_bus.py -->

Publish an event group and consume its completed states.

## Source

```python
"""Publish an event group and consume its completed states."""

import asyncio

from fastsprout.events import Event, EventBus, sub
from fastsprout.events.event import EventResult

bus = EventBus()


class BaseHeroEvent(Event):
    name: str
    power: str


class HeroEventA(BaseHeroEvent):
    pass


class HeroEventB(BaseHeroEvent):
    pass


class HeroEventC(BaseHeroEvent):
    pass


class HeroEventD(BaseHeroEvent):
    pass


class HeroEventE(BaseHeroEvent):
    pass


class HeroEventF(BaseHeroEvent):
    pass


@sub(
    HeroEventA,
    HeroEventB,
    HeroEventC,
    HeroEventD,
    HeroEventE,
    HeroEventF,
    bus=bus,
)
async def sub_handler(
    e: (
        HeroEventA
        | HeroEventB
        | HeroEventC
        | HeroEventD
        | HeroEventE
        | HeroEventF
    ),
) -> None:
    print("HeroEvent type:", type(e))
    return None


async def main():
    completed = []
    async with bus(
        HeroEventA(name="Spider-Man", power="spider"),
        HeroEventB(name="Batman", power="money"),
        HeroEventC(name="SuperMan", power="sun"),
        HeroEventD(name="Spider-Man", power="spider"),
        HeroEventE(name="Batman", power="money"),
        HeroEventF(name="SuperMan", power="sun"),
    ) as event_group_in_bus:
        async for event_state in event_group_in_bus.as_completed():
            event_result: EventResult[
                HeroEventA
                | HeroEventB
                | HeroEventC
                | HeroEventD
                | HeroEventE
                | HeroEventF
            ] = await event_state.wait()
            completed.append(type(event_result.state.event).__name__)
    print("Event Results:", sorted(completed))


asyncio.run(main())
```

## Result

```text
HeroEvent type: <class '__main__.HeroEventA'>
HeroEvent type: <class '__main__.HeroEventB'>
HeroEvent type: <class '__main__.HeroEventC'>
HeroEvent type: <class '__main__.HeroEventD'>
HeroEvent type: <class '__main__.HeroEventE'>
HeroEvent type: <class '__main__.HeroEventF'>
Event Results: ['HeroEventA', 'HeroEventB', 'HeroEventC', 'HeroEventD', 'HeroEventE', 'HeroEventF']
```
