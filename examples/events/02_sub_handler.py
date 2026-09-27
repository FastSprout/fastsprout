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
    print("Event Result:", tuple(event_result))


asyncio.run(main())
