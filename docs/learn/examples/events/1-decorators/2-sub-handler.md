# 2. Sub Handler

<!-- example-source: examples/events/01_decorators_02_sub_handler.py -->

Subscribe a handler and wait for its event result.

## Source

```python
"""Subscribe a handler and wait for its event result."""

import asyncio

from fastsprout.events import Event, EventBus, EventState, sub

bus = EventBus()


class HeroEvent(Event):
    name: str
    power: str


@sub(HeroEvent, bus=bus)
async def process_hero_event(e: HeroEvent) -> None:
    print("HeroEvent:", e)
    return None


async def main():
    event_state: EventState[HeroEvent] = await bus.publish(
        HeroEvent(name="Batman", power="money")
    )

    event_result = await event_state.wait()
    print("Event Result:", event_result)


asyncio.run(main())
```

## Result

```text
HeroEvent: name='Batman' power='money'
Event Result: EventResult(state=EventState(event=HeroEvent(name='Batman', power='money')), values=[], pending=0, errors=[])
```
