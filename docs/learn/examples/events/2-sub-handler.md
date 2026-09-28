# 2. Sub Handler

<!-- example-source: examples/events/02_sub_handler.py -->

`@sub(HeroEvent)` registers a handler for that event type. `bus.publish()` returns an `EventState`; awaiting `state.wait()` waits for the subscribed handler and returns its `EventResult`.

Run from the repository root:

```bash
uv run --extra events python examples/events/02_sub_handler.py
```

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

The handler prints the event and its result. The result contains no returned
values or pending handlers because the subscriber returns `None`.

```text
HeroEvent: name='Batman' power='money'
Event Result: EventResult(state=EventState(event=HeroEvent(name='Batman', power='money')), values=[], pending=0, errors=[])
```
