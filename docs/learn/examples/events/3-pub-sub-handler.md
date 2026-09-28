# 3. Pub Sub Handler

<!-- example-source: examples/events/03_pub_sub_handler.py -->

A handler can both subscribe and publish. Here receiving `SubHeroEvent` runs `pub_sub_handler`, which returns a new `PubHeroEvent`. The example waits for the first event and then looks up the second event's state.

Run from the repository root:

```bash
uv run --extra events python examples/events/03_pub_sub_handler.py
```

## Source

```python
"""Publish a second event from a subscribed handler."""

import asyncio
from collections.abc import AsyncIterator

from fastsprout.events import Event, EventBus, EventResult, EventState, pub, sub

bus = EventBus()


class SubHeroEvent(Event):
    name: str
    power: str


class PubHeroEvent(SubHeroEvent):
    sub: SubHeroEvent


@sub(SubHeroEvent, bus=bus)
@pub(bus=bus)
async def pub_sub_handler(e: SubHeroEvent) -> PubHeroEvent:
    return PubHeroEvent(sub=e, name=e.name, power=e.power)


async def main():
    first_event_state: EventState[SubHeroEvent] = await bus.publish(
        SubHeroEvent(name="Batman", power="money")
    )

    event_result: EventResult[SubHeroEvent] = await first_event_state.wait()
    print("Event Result:", event_result)

    second_event_state: AsyncIterator[EventState[PubHeroEvent]] = await bus.get(
        PubHeroEvent
    )

    print("Event State:", await anext(second_event_state))


asyncio.run(main())
```

## Result

The first handler returns one event, and the bus contains the published second event:

```text
Event Result: EventResult(state=EventState(event=SubHeroEvent(name='Batman', power='money')), values=[PubHeroEvent(name='Batman', power='money', sub=SubHeroEvent(name='Batman', power='money'))], pending=0, errors=[])
Event State: EventState(event=PubHeroEvent(name='Batman', power='money', sub=SubHeroEvent(name='Batman', power='money')))
```
